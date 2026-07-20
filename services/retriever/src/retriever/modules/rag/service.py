# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""RAG service orchestrating retrieval and generation."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.infrastructure.cache.protocol import CachedAnswer, SemanticCache
from retriever.infrastructure.embeddings.protocol import EmbeddingProvider
from retriever.infrastructure.llm.protocol import LLMProvider
from retriever.infrastructure.observability.langfuse import observe
from retriever.infrastructure.safety.confidence import ConfidenceScorer
from retriever.infrastructure.safety.service import SafetyService
from retriever.infrastructure.vectordb.protocol import (
    ChunkInput,
    SearchResult,
    VectorStore,
)
from retriever.modules.rag.prompts import FALLBACK_SYSTEM_PROMPT, build_rag_prompt
from retriever.modules.rag.retriever import HybridRetriever
from retriever.modules.rag.schemas import (
    Chunk,
    ChunkWithScore,
    DocumentProcessor,
    IndexingResult,
    RAGResponse,
)

logger = structlog.get_logger()

# Single, undifferentiated reason surfaced to callers when a request is
# blocked by any safety rail. The specific SafetyViolationType stays in
# server-side logs only: returning it lets a caller tell which layer fired
# (prompt injection vs moderation vs hallucination) and tune bypass attempts
# against that 3-way oracle. See issue #255.
BLOCKED_REASON = "blocked"


def _serialize_sources(chunks: list[ChunkWithScore]) -> list[dict[str, Any]]:
    """Serialize chunks to dicts for caching.

    Args:
        chunks: List of scored chunks to serialize.

    Returns:
        List of dictionaries suitable for cache storage.
    """
    return [
        {
            "content": c.content,
            "source": c.source,
            "section": c.section,
            "score": c.score,
            "title": c.title,
        }
        for c in chunks
    ]


def _deserialize_sources(sources: list[dict[str, Any]]) -> list[ChunkWithScore]:
    """Deserialize cached sources back to ChunkWithScore objects.

    Args:
        sources: List of source dicts from cache.

    Returns:
        List of ChunkWithScore instances.
    """
    return [
        ChunkWithScore(
            content=str(s["content"]),
            source=str(s["source"]),
            section=str(s.get("section", "")),
            score=float(s.get("score", 0.0)),
            title=str(s.get("title", "")),
        )
        for s in sources
    ]


class RAGService:
    """Orchestrates the RAG pipeline: retrieve relevant chunks, generate answer.

    The RAG service coordinates:
    - Document indexing (process, embed, store)
    - Question answering (embed query, retrieve, generate)
    - Safety checks (moderation, injection, hallucination)
    - Confidence scoring and caching
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        llm_provider: LLMProvider,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        document_processor: DocumentProcessor,
        *,
        semantic_cache: SemanticCache | None = None,
        hybrid_retriever: HybridRetriever | None = None,
        safety_service: SafetyService | None = None,
        confidence_scorer: ConfidenceScorer | None = None,
        top_k: int = 5,
        tenant_id: uuid.UUID | None = None,
    ) -> None:
        """Initialize the RAG service.

        Args:
            session_factory: Async SQLAlchemy session factory.
            llm_provider: Provider for generating answers.
            embedding_provider: Provider for generating embeddings.
            vector_store: Store for document chunks.
            document_processor: Combined document parser and chunker.
            semantic_cache: Optional cache for similar question lookups.
            hybrid_retriever: Optional hybrid retriever combining semantic
                and keyword search.
            safety_service: Optional safety service for content moderation
                and hallucination detection.
            confidence_scorer: Optional scorer for answer confidence.
            top_k: Number of chunks to retrieve per query.
            tenant_id: Default tenant ID for multi-tenant scoping.
        """
        self._session_factory = session_factory
        self._llm = llm_provider
        self._embeddings = embedding_provider
        self._store = vector_store
        self._processor = document_processor
        self._cache = semantic_cache
        self._retriever = hybrid_retriever
        self._safety = safety_service
        self._confidence_scorer = confidence_scorer or ConfidenceScorer()
        self._top_k = top_k
        self._tenant_id = tenant_id

    async def _screen_history(
        self,
        conversation_history: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Re-screen prior conversation turns before they are replayed.

        Only the newest question passes through ``check_input`` on each turn;
        stored history would otherwise be appended verbatim to every later
        model call, recirculating anything that entered the conversation
        unscreened (for example via the retrieved-chunk path). Each stored
        turn's content is re-screened here with the same input check, and
        unsafe turns are dropped and logged, mirroring retrieved-chunk
        screening. See issue #256.

        Args:
            conversation_history: Prior messages as
                [{"role": "user"|"assistant", "content": "..."}].

        Returns:
            The screened history with unsafe turns removed (possibly empty).
        """
        if self._safety is None:
            return conversation_history

        screened: list[dict[str, str]] = []
        dropped = 0
        for message in conversation_history:
            check = await self._safety.check_input(message.get("content", ""))
            if check.is_safe:
                screened.append(message)
            else:
                dropped += 1
                logger.warning(
                    "rag_history_turn_screened_out",
                    role=message.get("role", "unknown"),
                    violation_type=check.violation_type.value,
                )
        if dropped:
            logger.warning(
                "rag_history_screened_out",
                dropped_count=dropped,
                total_count=len(conversation_history),
            )
        return screened

    @observe()  # type: ignore[untyped-decorator]
    async def ask(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> RAGResponse:
        """Answer a question using RAG with optional conversation history.

        Pipeline:
        1. Input safety check (if safety_service)
        2. Embed query
        3. Cache lookup (if semantic_cache)
        4. Retrieve chunks (hybrid or semantic-only)
        5. Build prompt with context
        5b. Re-screen stored conversation history (if safety_service)
        6. Generate answer via LLM
        7. Output moderation check (if safety_service)
        8. Hallucination check (if safety_service)
        9. Confidence scoring
        10. Cache set (if high/medium confidence)
        11. Return RAGResponse

        Args:
            question: The user's question.
            conversation_history: Optional list of prior messages as
                [{"role": "user"|"assistant", "content": "..."}].

        Returns:
            RAGResponse with answer and retrieved chunks.
        """
        # 1. Check input safety first (if enabled)
        if self._safety is not None:
            safety_result = await self._safety.check_input(question)
            if not safety_result.is_safe:
                logger.warning(
                    "rag_input_blocked",
                    violation_type=safety_result.violation_type.value,
                    question_length=len(question),
                )
                return RAGResponse(
                    answer=safety_result.message,
                    chunks_used=[],
                    question=question,
                    confidence_level="low",
                    confidence_score=0.0,
                    blocked=True,
                    blocked_reason=BLOCKED_REASON,
                )

        # 2. Embed query — MUST happen before cache lookup
        #    (new cache takes embedding, not text)
        query_embedding = await self._embeddings.embed(question)

        # 3. Cache lookup (if enabled)
        if self._cache is not None and self._tenant_id is not None:
            cached: CachedAnswer | None = await self._cache.get(
                query_embedding, self._tenant_id
            )
            if cached is not None:
                logger.info(
                    "rag_cache_hit",
                    question_length=len(question),
                )
                return RAGResponse(
                    answer=cached["answer"],
                    chunks_used=_deserialize_sources(cached["sources"]),
                    question=question,
                    confidence_level="high",
                    confidence_score=0.9,
                )

        # 4. Retrieve chunks
        results: list[SearchResult]
        if self._retriever is not None and self._tenant_id is not None:
            # Hybrid retrieval (semantic + keyword search with RRF)
            logger.debug("rag_hybrid_retrieving", top_k=self._top_k)
            results = await self._retriever.retrieve(
                query_embedding,
                question,
                self._tenant_id,
                top_k=self._top_k,
            )
        elif self._tenant_id is not None:
            # Semantic-only search
            logger.debug("rag_semantic_retrieving", top_k=self._top_k)
            results = await self._store.search(
                query_embedding,
                self._tenant_id,
                limit=self._top_k,
                min_score=0.3,
            )
        else:
            results = []

        # 4b. Screen retrieved chunk content before it reaches the
        #     SYSTEM-role prompt. Retrieved content is untrusted (it may
        #     have been injected into a shelter document by an attacker),
        #     so it gets the same screening as end-user input before it
        #     can influence the model.
        if self._safety is not None and results:
            screened_results: list[SearchResult] = []
            dropped = 0
            for result_item in results:
                chunk_check = await self._safety.check_input(result_item["content"])
                if chunk_check.is_safe:
                    screened_results.append(result_item)
                else:
                    dropped += 1
                    logger.warning(
                        "rag_chunk_screened_out",
                        source=result_item["source"],
                        violation_type=chunk_check.violation_type.value,
                        stage="query",
                    )
            if dropped:
                logger.warning(
                    "rag_chunks_screened_out",
                    dropped_count=dropped,
                    total_count=len(results),
                    stage="query",
                )
            results = screened_results

        # 5b. Re-screen stored conversation history before it is replayed into
        #     the generation call (see _screen_history). Only the newest
        #     question is screened at input; prior turns would otherwise be
        #     appended verbatim on every turn, recirculating unscreened content.
        #     Placed after the cache lookup so a cache hit skips this work.
        if self._safety is not None and conversation_history:
            conversation_history = await self._screen_history(conversation_history)

        # If no chunks found, use fallback prompt
        if not results:
            logger.info("rag_no_documents", question_length=len(question))
            if conversation_history:
                messages = conversation_history.copy()
                messages.append({"role": "user", "content": question})
                answer = await self._llm.complete_with_history(
                    system_prompt=FALLBACK_SYSTEM_PROMPT,
                    messages=messages,
                )
            else:
                answer = await self._llm.complete(
                    system_prompt=FALLBACK_SYSTEM_PROMPT,
                    user_message=question,
                )

            # Moderate the generated answer before it reaches the user.
            if self._safety is not None:
                output_result = await self._safety.check_output(answer)
                if not output_result.is_safe:
                    logger.warning(
                        "rag_output_blocked",
                        question_length=len(question),
                        answer_length=len(answer),
                    )
                    return RAGResponse(
                        answer=output_result.message,
                        chunks_used=[],
                        question=question,
                        confidence_level="low",
                        confidence_score=0.0,
                        blocked=True,
                        blocked_reason=BLOCKED_REASON,
                    )

            return RAGResponse(
                answer=answer,
                chunks_used=[],
                question=question,
            )

        # Convert SearchResult list to ChunkWithScore
        chunks_used = [ChunkWithScore.from_search_result(r) for r in results]

        # 5. Build context prompt
        context_tuples: list[tuple[str, str, float]] = [
            (r["content"], r["source"], r["score"]) for r in results
        ]
        system_prompt = build_rag_prompt(context_tuples)

        # 6. Generate answer
        logger.debug(
            "rag_generating",
            context_chunks=len(results),
            question_length=len(question),
            has_history=conversation_history is not None,
            history_length=len(conversation_history) if conversation_history else 0,
        )

        if conversation_history:
            messages = conversation_history.copy()
            messages.append({"role": "user", "content": question})
            answer = await self._llm.complete_with_history(
                system_prompt=system_prompt,
                messages=messages,
            )
        else:
            answer = await self._llm.complete(
                system_prompt=system_prompt,
                user_message=question,
            )

        # 7. Output moderation check (before hallucination check)
        if self._safety is not None:
            output_result = await self._safety.check_output(answer)
            if not output_result.is_safe:
                logger.warning(
                    "rag_output_blocked",
                    question_length=len(question),
                    answer_length=len(answer),
                )
                return RAGResponse(
                    answer=output_result.message,
                    chunks_used=chunks_used,
                    question=question,
                    confidence_level="low",
                    confidence_score=0.0,
                    blocked=True,
                    blocked_reason=BLOCKED_REASON,
                )

        # 8. Hallucination check and get grounding ratio
        grounding_ratio: float | None = None
        chunk_texts = [c.content for c in chunks_used]

        if self._safety is not None and chunks_used:
            hallucination_result = self._safety.check_hallucination(
                answer=answer,
                chunks=chunk_texts,
                sources=[c.source for c in chunks_used],
            )
            if not hallucination_result.is_safe:
                logger.warning(
                    "rag_hallucination_detected",
                    question_length=len(question),
                )
                return RAGResponse(
                    answer=hallucination_result.message,
                    chunks_used=chunks_used,
                    question=question,
                    confidence_level="low",
                    confidence_score=0.0,
                    blocked=True,
                    blocked_reason=BLOCKED_REASON,
                )

            # Get grounding ratio for confidence scoring
            details = self._safety.get_hallucination_details(
                answer=answer,
                chunks=chunk_texts,
            )
            grounding_ratio = details.support_ratio

        # 9. Confidence scoring
        scores = [c.score for c in chunks_used]
        confidence = self._confidence_scorer.score(
            chunk_scores=scores,
            grounding_ratio=grounding_ratio,
        )

        # Log quality metrics
        sources_used = list({c.source for c in chunks_used})
        logger.info(
            "rag_answer_generated",
            question_length=len(question),
            answer_length=len(answer),
            chunks_used=len(chunks_used),
            sources_used=sources_used,
            top_score=max(scores) if scores else 0.0,
            min_score=min(scores) if scores else 0.0,
            avg_score=sum(scores) / len(scores) if scores else 0.0,
            confidence_level=confidence.level.value,
            confidence_score=confidence.score,
        )

        # 10. Cache set (only high/medium confidence answers with context)
        if (
            self._cache is not None
            and self._tenant_id is not None
            and chunks_used
            and not confidence.needs_review
        ):
            await self._cache.set(
                query=question,
                query_embedding=query_embedding,
                answer=answer,
                sources=_serialize_sources(chunks_used),
                tenant_id=self._tenant_id,
            )

        # 11. Return response
        return RAGResponse(
            answer=answer,
            chunks_used=chunks_used,
            question=question,
            confidence_level=confidence.level.value,
            confidence_score=confidence.score,
        )

    @observe()  # type: ignore[untyped-decorator]
    async def index_document(
        self,
        document_id: uuid.UUID,
        content: bytes,
        source: str,
        title: str,
    ) -> IndexingResult:
        """Index a document into the vector store.

        Processes the raw bytes through the document processor (parse + chunk),
        generates embeddings, and upserts into the store. CPU-bound Docling
        processing runs in a thread to avoid blocking the event loop.

        Args:
            document_id: UUID of the document record.
            content: Raw file bytes.
            source: Source filename or identifier.
            title: Document title (fallback — processor may extract a better one).

        Returns:
            IndexingResult with status, chunk count, and parsed title.
        """
        try:
            # 1. Process document (parse + chunk) in a thread
            #    Docling's convert() is sync and CPU-bound
            result = await asyncio.to_thread(self._processor.process, content, source)
            chunks = result.chunks

            if not chunks:
                return IndexingResult(
                    source=source,
                    chunks_created=0,
                    success=True,
                    parsed_title=result.document.title,
                )

            # 1b. Screen chunk content before it is embedded and stored.
            #     Document content is untrusted (it may contain injected
            #     instructions), so it gets the same screening as
            #     query-time retrieved chunks before it enters the index.
            if self._safety is not None:
                screened_chunks: list[Chunk] = []
                dropped = 0
                for chunk in chunks:
                    check_result = await self._safety.check_input(chunk.content)
                    if check_result.is_safe:
                        screened_chunks.append(chunk)
                    else:
                        dropped += 1
                        logger.warning(
                            "rag_chunk_screened_out",
                            source=source,
                            violation_type=check_result.violation_type.value,
                            stage="ingest",
                        )
                if dropped:
                    logger.warning(
                        "rag_chunks_screened_out",
                        dropped_count=dropped,
                        total_count=len(chunks),
                        stage="ingest",
                    )
                chunks = screened_chunks

                if not chunks:
                    return IndexingResult(
                        source=source,
                        chunks_created=0,
                        success=True,
                        parsed_title=result.document.title,
                    )

            # 2. Embed batch
            logger.debug(
                "rag_embedding_chunks",
                source=source,
                chunk_count=len(chunks),
            )
            contents = [chunk.content for chunk in chunks]
            embeddings = await self._embeddings.embed_batch(contents)

            # 3. Build ChunkInput list
            chunk_inputs: list[ChunkInput] = [
                ChunkInput(
                    document_id=document_id,
                    content=chunk.content,
                    embedding=embedding,
                    source=source,
                    title=result.document.title,
                )
                for chunk, embedding in zip(chunks, embeddings, strict=True)
            ]

            # 4. Upsert into vector store
            if self._tenant_id is not None:
                await self._store.upsert(chunk_inputs, self._tenant_id)
            else:
                # Use a default tenant for non-multi-tenant setups
                default_tenant = uuid.UUID("00000000-0000-0000-0000-000000000000")
                await self._store.upsert(chunk_inputs, default_tenant)

            logger.info(
                "rag_document_indexed",
                source=source,
                chunks_created=len(chunks),
                document_id=str(document_id),
            )

            return IndexingResult(
                source=source,
                chunks_created=len(chunks),
                success=True,
                parsed_title=result.document.title,
            )

        except Exception as exc:
            logger.error(
                "rag_index_error",
                source=source,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return IndexingResult(
                source=source,
                chunks_created=0,
                success=False,
                error_message=f"Indexing failed: {exc}",
            )

    async def clear_cache(self, tenant_id: uuid.UUID | None = None) -> None:
        """Clear the semantic cache for a tenant.

        Args:
            tenant_id: Tenant to clear cache for. Falls back to default tenant.
        """
        if self._cache is not None:
            tid = tenant_id or self._tenant_id
            if tid is not None:
                await self._cache.invalidate(tid)
                logger.info("rag_cache_cleared", tenant_id=str(tid))

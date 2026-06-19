# 019: Docling Document Processing

**Status:** Accepted
**Date:** 2026-03-16
**Supersedes:** Custom TextDocumentParser + HierarchicalChunker

## Context

Retriever's document processing handled only `.md` and `.txt` files via custom `TextDocumentParser` and `HierarchicalChunker` with character-based splitting (1500 chars, 800 overlap). The old monolith had broader format support via Docling that was intentionally stripped during the FastAPI stack migration (Phases 1-8) to keep scope tight. The protocols were designed for this swap.

## Decision

Replace the custom parser + chunker with Docling, gaining:
- Multi-format support: PDF, DOCX, PPTX, XLSX, HTML, images
- Token-aware chunking via `HybridChunker` with `OpenAITokenizer` aligned to `text-embedding-3-small`
- ML-powered layout understanding for PDFs (DocLayNet), table extraction (TableFormer), and optional OCR (EasyOCR)
- Heading-contextualized chunks via `contextualize()` for better embedding quality

### Key Architecture Decisions

**Combined `process()` method:** New `DocumentProcessor` protocol with single `process(content: bytes, source: str) -> ProcessingResult` replaces separate `DocumentParser.parse()` + `DocumentChunker.chunk()`. Avoids caching `DoclingDocument` between calls.

**Text-only fast path:** `FormatAwareProcessor` routes `.md`/`.txt` through Docling's lightweight `SimplePipeline` (no ML models loaded). Binary formats go through `DoclingProcessor` with full ML pipeline, lazy-initialized on first binary upload.

**Token budget:** 512 tokens per chunk, inclusive of heading context from `contextualize()`. Heading overhead (~15-30 tokens) reduces content tokens but improves retrieval quality. Configurable via `docling_chunk_max_tokens`.

**Lazy imports:** All Docling imports are inside methods, not at module level. PyTorch (~800 MB) only loads when the first binary document is uploaded.

**Async bridge:** `DocumentProcessor.process()` is sync (matching Docling's API). `RAGService.index_document()` wraps it with `asyncio.to_thread()`. A `threading.Lock` inside `DoclingProcessor` protects `converter.convert()`.

**CPU-only PyTorch:** Container uses `--index-url https://download.pytorch.org/whl/cpu` to avoid CUDA dependencies.

## Consequences

**Positive:**
- 10+ document formats supported (up from 2)
- Token-aware chunking aligned with embedding model
- Structure-preserving parsing (headings, tables, lists)
- Heading context in embeddings improves retrieval for section-level queries
- GIN full-text index benefits from heading terms in chunks

**Negative:**
- PyTorch dependency increases container size (~500 MB for CPU-only)
- ML model init takes 5-30 seconds on first binary upload
- Requires `HF_HOME` caching in CI for reproducible builds

**Risks:**
- Docling API changes between major versions could break the adapter (mitigated by version pinning `>=2.0`)
- `do_picture_description` is off by default due to VLM model size — images are silently skipped

## Files Changed

- **Deleted:** `chunker.py` (custom HierarchicalChunker), `TextDocumentParser` class
- **New:** `docling_processor.py`, `exceptions.py`
- **Modified:** `schemas.py`, `service.py`, `loader.py`, `dependencies.py`, `config.py`, `prompts.py`, `documents/services.py`

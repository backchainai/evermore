# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""A dependency-light, OpenAI-compatible LLM gateway stub for local development.

Stands in for the Cloudflare AI Gateway so the full stack runs locally with no
paid credentials and no network. Point a service at it with::

    LLM_GATEWAY_URL=http://localhost:8099/v1

It serves the three OpenAI-compatible endpoints the Retriever uses, matched by
path suffix so any base path (``/v1``, Cloudflare's ``/compat``, etc.) works:

    POST .../chat/completions   canned assistant reply that echoes the prompt
    POST .../embeddings         deterministic, unit-normalized 1536-dim vectors
    POST .../moderations        always-safe result over the omni category set

Answers are fake by design; the point is an end-to-end loop, not real inference.
Embeddings are deterministic (seeded by the input text) so the same text always
maps to the same vector, which keeps the pgvector cache and similarity search
behaving consistently across runs.

Run it directly with the system Python (standard library only, no venv)::

    python3 tools/llm-stub/llm_stub.py --port 8099

Environment overrides: ``LLM_STUB_PORT`` (port), ``LLM_STUB_HOST`` (bind host).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# The Retriever pins the embedding column to 1536 (text-embedding-3-small) in
# both the pgvector store and the cache, so the stub must match exactly.
EMBEDDING_DIM = 1536

# Full omni-moderation category set. Providing every key the OpenAI SDK expects
# keeps `category_scores` free of None values (the caller calls float() on each).
MODERATION_CATEGORIES = (
    "harassment",
    "harassment/threatening",
    "hate",
    "hate/threatening",
    "illicit",
    "illicit/violent",
    "self-harm",
    "self-harm/intent",
    "self-harm/instructions",
    "sexual",
    "sexual/minors",
    "violence",
    "violence/graphic",
)

# The moderation response is constant, so build the category maps once. They are
# only ever JSON-serialized (never mutated), so sharing the objects is safe.
MODERATION_CATEGORIES_FALSE = {c: False for c in MODERATION_CATEGORIES}
MODERATION_CATEGORY_SCORES_ZERO = {c: 0.0 for c in MODERATION_CATEGORIES}


def deterministic_embedding(text: str) -> list[float]:
    """Return a stable, unit-normalized 1536-dim vector for ``text``.

    A SHA-256 of the text seeds a small xorshift PRNG, so the vector is
    reproducible across processes and runs without depending on a global RNG.
    """
    seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
    state = seed or 1  # xorshift must not start at zero
    values: list[float] = []
    sumsq = 0.0
    for _ in range(EMBEDDING_DIM):
        state ^= (state << 13) & 0xFFFFFFFFFFFFFFFF
        state ^= state >> 7
        state ^= (state << 17) & 0xFFFFFFFFFFFFFFFF
        # Map the 64-bit state into [-1, 1).
        v = (state / 0xFFFFFFFFFFFFFFFF) * 2.0 - 1.0
        values.append(v)
        sumsq += v * v
    norm = math.sqrt(sumsq) or 1.0
    return [v / norm for v in values]


def chat_reply(payload: dict) -> str:
    """Build a canned assistant reply that echoes the latest user message."""
    messages = payload.get("messages") or []
    last_user = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            last_user = str(message.get("content") or "")
            break
    preview = last_user.strip().replace("\n", " ")
    if len(preview) > 300:
        preview = preview[:300] + "…"
    return (
        "[local LLM stub] This is a placeholder answer from the offline gateway "
        "stub; no real model was called. "
        + (f'You asked: "{preview}"' if preview else "No user message was found.")
    )


class StubHandler(BaseHTTPRequestHandler):
    """Routes OpenAI-compatible POSTs by path suffix; everything else 404s."""

    server_version = "llm-stub/1.0"

    def _send_json(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_payload(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        # A trivial liveness probe for `make` / scripts to poll.
        if self.path.rstrip("/").endswith("/health") or self.path in ("/", ""):
            self._send_json(200, {"status": "ok", "service": "llm-stub"})
            return
        self._send_json(404, {"error": {"message": f"no such path: {self.path}"}})

    def do_POST(self) -> None:  # noqa: N802 (http.server API)
        path = self.path.split("?", 1)[0].rstrip("/")
        payload = self._read_payload()
        model = str(payload.get("model") or "stub-model")

        if path.endswith("/chat/completions"):
            self._send_json(
                200,
                {
                    "id": "chatcmpl-stub",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": chat_reply(payload),
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                },
            )
            return

        if path.endswith("/embeddings"):
            raw_input = payload.get("input", "")
            inputs = raw_input if isinstance(raw_input, list) else [raw_input]
            data = [
                {
                    "object": "embedding",
                    "index": index,
                    "embedding": deterministic_embedding(str(item)),
                }
                for index, item in enumerate(inputs)
            ]
            self._send_json(
                200,
                {
                    "object": "list",
                    "data": data,
                    "model": model,
                    "usage": {"prompt_tokens": 0, "total_tokens": 0},
                },
            )
            return

        if path.endswith("/moderations"):
            self._send_json(
                200,
                {
                    "id": "modr-stub",
                    "model": model,
                    "results": [
                        {
                            "flagged": False,
                            "categories": MODERATION_CATEGORIES_FALSE,
                            "category_scores": MODERATION_CATEGORY_SCORES_ZERO,
                        }
                    ],
                },
            )
            return

        self._send_json(404, {"error": {"message": f"no such path: {self.path}"}})

    def log_message(self, fmt: str, *args) -> None:  # noqa: ANN002
        # Keep the stub quiet but useful: one concise line per request on stderr.
        sys.stderr.write("llm-stub %s\n" % (fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenAI-compatible LLM stub.")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("LLM_STUB_PORT", "8099")),
        help="Port to listen on (default 8099, or $LLM_STUB_PORT).",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("LLM_STUB_HOST", "127.0.0.1"),
        help="Host to bind (default 127.0.0.1, or $LLM_STUB_HOST).",
    )
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), StubHandler)
    sys.stderr.write(
        f"llm-stub listening on http://{args.host}:{args.port} "
        f"(point LLM_GATEWAY_URL at http://{args.host}:{args.port}/v1)\n"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

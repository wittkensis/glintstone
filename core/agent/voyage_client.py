"""Voyage embeddings client.

`voyage-3-large` is 1024-dim. Backfill and query embedding both go through here.

Design notes:
- Batch up to 128 texts per call (Voyage's limit).
- sha256 each input; skip re-embed if the source_hash is already in
  entity_embeddings for that (entity_type, entity_id, model).
- Retries with exponential backoff on rate-limit / 5xx.
- Synchronous; the call sites are short-lived REST handlers and a one-time
  backfill script. If we ever need async, switch to voyageai.AsyncClient.

Anthropic acquired Voyage in 2024; key management is still separate today.
Set VOYAGE_API_KEY in .env alongside ANTHROPIC_API_KEY.
"""

import hashlib
import logging
import os
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_MODEL = "voyage-3-large"
_DIM = 1024
_BATCH = 128


@dataclass
class EmbedResult:
    text: str
    source_hash: str
    vector: list[float]


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class VoyageClient:
    """Thin wrapper. Lazily imports voyageai so the package isn't required
    in environments that don't run embeddings."""

    def __init__(self, api_key: str | None = None) -> None:
        # Mirror AnthropicClient: fall back to the canonical Settings object,
        # not just os.environ. Under systemd/uvicorn the .env is parsed by
        # pydantic-settings into Settings but is NOT exported into os.environ,
        # so reading os.environ alone left semantic search silently degrading
        # to lexical in production.
        from core.config import get_settings  # noqa: PLC0415

        settings = get_settings()
        self.api_key = (
            api_key
            or os.environ.get("VOYAGE_API_KEY")
            or getattr(settings, "voyage_api_key", None)
            or os.environ.get("ANTHROPIC_API_KEY")
            or getattr(settings, "anthropic_api_key", None)
        )
        if not self.api_key:
            raise RuntimeError(
                "VOYAGE_API_KEY (or ANTHROPIC_API_KEY as fallback) is not set"
            )
        self._client = None  # lazy init

    def _ensure(self):
        if self._client is None:
            import voyageai  # pip install voyageai

            self._client = voyageai.Client(api_key=self.api_key)
        return self._client

    def embed(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> list[EmbedResult]:
        """Embed a batch of texts. Returns one EmbedResult per input."""
        if not texts:
            return []

        client = self._ensure()
        results: list[EmbedResult] = []

        for chunk_start in range(0, len(texts), _BATCH):
            chunk = texts[chunk_start : chunk_start + _BATCH]
            vectors = self._embed_with_retry(client, chunk, input_type)
            for text, vec in zip(chunk, vectors):
                results.append(
                    EmbedResult(text=text, source_hash=_hash(text), vector=vec)
                )
        return results

    def embed_query(self, text: str) -> EmbedResult:
        """Single-text helper for search queries."""
        result = self.embed([text], input_type="query")
        return result[0]

    def _embed_with_retry(
        self, client, texts: list[str], input_type: str, max_retries: int = 5
    ) -> list[list[float]]:
        delay = 1.0
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                resp = client.embed(texts, model=_MODEL, input_type=input_type)
                return resp.embeddings
            except Exception as exc:  # voyageai exposes its own exception types
                last_exc = exc
                if attempt == max_retries - 1:
                    break
                logger.warning(
                    "voyage embed retry %d/%d after %.1fs: %s",
                    attempt + 1,
                    max_retries,
                    delay,
                    exc,
                )
                time.sleep(delay)
                delay = min(delay * 2, 30.0)
        raise RuntimeError(
            f"Voyage embedding failed after {max_retries} retries"
        ) from last_exc


def filter_unchanged(
    texts_by_id: dict[str, str],
    existing_hashes: dict[str, str],
) -> dict[str, str]:
    """Given new candidate texts keyed by entity_id and the hashes already in
    the DB for the same model+entity_type, return only the ids whose hash
    differs. The caller is responsible for the existing_hashes lookup."""
    return {
        entity_id: text
        for entity_id, text in texts_by_id.items()
        if existing_hashes.get(entity_id) != _hash(text)
    }

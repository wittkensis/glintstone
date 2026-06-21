"""Anthropic client wrapper for grounded synthesis.

Design notes:
- Sonnet 4.6 is the default (see decisions.md). Hero scenarios are constrained
  generation, not open-ended reasoning; Sonnet is plenty.
- Adaptive thinking on. Effort 'medium' — synthesis is bounded.
- System prompt cached via top-level cache_control: {"type": "ephemeral"}.
  We pass system as a list of text blocks with cache_control on the last block.
- Returns plain text. The caller parses [n] markers (citation_parser.py).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_MAX_TOKENS = 2048


@dataclass
class CompletionResult:
    text: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    model: str
    stop_reason: str

    @property
    def cache_hit(self) -> bool:
        return self.cache_read_tokens > 0


class AnthropicClient:
    """Lazy-init wrapper around anthropic.Anthropic."""

    def __init__(self, api_key: str | None = None, model: str = _DEFAULT_MODEL) -> None:
        from core.config import get_settings  # noqa: PLC0415

        settings = get_settings()
        self.api_key = (
            api_key
            or os.environ.get("ANTHROPIC_API_KEY")
            or getattr(settings, "anthropic_api_key", None)
        )
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.model = model
        self._client = None

    def _ensure(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        effort: str = "medium",
        timeout: float = 120.0,
    ) -> CompletionResult:
        """Single Claude call with prompt caching on the system prompt.

        The user_message changes per artifact/token; the system_prompt does not.
        cache_control on the system block means second-and-later calls within
        the 5-minute TTL pay only ~0.1× for the system tokens.
        """
        client = self._ensure()
        response = client.with_options(timeout=timeout).messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
        )

        text = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        )

        return CompletionResult(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_read_tokens=response.usage.cache_read_input_tokens or 0,
            cache_creation_tokens=response.usage.cache_creation_input_tokens or 0,
            model=response.model,
            stop_reason=response.stop_reason or "",
        )

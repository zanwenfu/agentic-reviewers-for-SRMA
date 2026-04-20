"""Thin wrapper around the OpenAI Chat Completions API.

Isolates network + retry logic so the agents stay declarative, and tracks
per-call token cost so a full SRMA run can report an honest dollar figure.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable

from openai import OpenAI

from .config import settings

logger = logging.getLogger(__name__)


# Published prices per 1K tokens (2025). Override by editing here if OpenAI
# restructures pricing — the cost math is simple enough to not need a lookup
# service.
_PRICE_PER_1K = {
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "o3-mini": {"prompt": 0.0011, "completion": 0.0044},
}


@dataclass
class CallResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    model: str


class LLM:
    """A model-agnostic chat client with retry + cost tracking."""

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set — copy .env.example to .env and fill it in."
            )
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.total_cost_usd = 0.0

    def complete(
        self,
        model: str,
        user: str,
        *,
        system: str | None = None,
        history: Iterable[dict] | None = None,
    ) -> CallResult:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user})

        last_err: Exception | None = None
        for attempt in range(1, settings.max_retries + 1):
            try:
                resp = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    timeout=settings.request_timeout_s,
                )
                usage = resp.usage
                cost = _price(model, usage.prompt_tokens, usage.completion_tokens)
                self.total_cost_usd += cost
                return CallResult(
                    text=resp.choices[0].message.content or "",
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    cost_usd=cost,
                    model=model,
                )
            except Exception as err:  # noqa: BLE001 — we're deliberately broad
                last_err = err
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s",
                    attempt,
                    settings.max_retries,
                    err,
                )
                if attempt < settings.max_retries:
                    time.sleep(settings.retry_backoff_s)

        raise RuntimeError(f"LLM call failed after retries: {last_err}") from last_err


def _price(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = _PRICE_PER_1K.get(model)
    if rates is None:
        logger.debug("No pricing table entry for model %s; cost recorded as 0.", model)
        return 0.0
    return (
        prompt_tokens * rates["prompt"] + completion_tokens * rates["completion"]
    ) / 1000.0

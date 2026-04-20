"""Runtime configuration for LUMINA.

Resolved once at import time from environment variables (or a `.env` file if
`python-dotenv` is installed). Downstream modules import `settings` directly.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # optional: .env support
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover — dotenv is optional
    pass


@dataclass(frozen=True)
class Settings:
    """Immutable configuration snapshot."""

    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    openai_base_url: str | None = field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL")
    )

    # Model selection — matches the NEJM AI manuscript.
    # Classifier / detailed screener / improver run on a cheap fast model.
    worker_model: str = field(
        default_factory=lambda: os.getenv("LUMINA_WORKER_MODEL", "gpt-4o-mini")
    )
    # Reviewer uses a stronger reasoning model to avoid rubber-stamping.
    reviewer_model: str = field(
        default_factory=lambda: os.getenv("LUMINA_REVIEWER_MODEL", "o3-mini")
    )

    request_timeout_s: int = 60
    max_retries: int = 3
    retry_backoff_s: int = 10

    # Safety valve on the reviewer ↔ improver loop so a pathological
    # disagreement cannot burn tokens forever.
    max_review_iterations: int = 3

    log_level: str = field(
        default_factory=lambda: os.getenv("LUMINA_LOG_LEVEL", "INFO")
    )

    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)


settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)

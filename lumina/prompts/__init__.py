"""Prompt templates for the four LUMINA agents.

Prompts are kept as plain-text files under this directory so that clinicians
and reviewers without Python experience can inspect and edit them directly.
"""
from pathlib import Path
from typing import Final

_PROMPT_DIR: Final = Path(__file__).parent


def load(name: str) -> str:
    """Read a prompt template by filename (without extension)."""
    path = _PROMPT_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


CLASSIFIER: Final = load("classifier")
CLASSIFIER_REVIEWER: Final = load("classifier_reviewer")
CLASSIFIER_IMPROVER: Final = load("classifier_improver")
DETAILED_SCREENER: Final = load("detailed_screener")
DETAILED_SCREENER_REVIEWER: Final = load("detailed_screener_reviewer")
DETAILED_SCREENER_IMPROVER: Final = load("detailed_screener_improver")
SYSTEM_MESSAGE: Final = load("system_message")

__all__ = [
    "load",
    "CLASSIFIER",
    "CLASSIFIER_REVIEWER",
    "CLASSIFIER_IMPROVER",
    "DETAILED_SCREENER",
    "DETAILED_SCREENER_REVIEWER",
    "DETAILED_SCREENER_IMPROVER",
    "SYSTEM_MESSAGE",
]

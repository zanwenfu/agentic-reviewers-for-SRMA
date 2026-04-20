"""The four LUMINA agents: Classifier, Detailed Screener, Reviewer, Improver.

Each agent is a thin function over an `LLM` + a prompt template. Parsing is
strict — the sentinel markers (`XXX`/`YYY`/`ZZZ`) from the original
manuscript are preserved here because they're what make the reviewer ↔
improver handshake deterministic.
"""
from __future__ import annotations

import logging
import re
from typing import Tuple

from . import prompts
from .config import settings
from .llm import LLM
from .types import (
    Candidate,
    ClassifierLabel,
    ScreeningLabel,
    SystematicReview,
)

logger = logging.getLogger(__name__)


_TRIPLE = re.compile(r"\b(XXX|YYY|ZZZ)\b", re.IGNORECASE)


def _extract_marker(text: str) -> str | None:
    """Return the last sentinel marker in `text`, or None if absent.

    We take the *last* match because the CoT response may quote the
    instruction ("output 'XXX' if ...") earlier in the body.
    """
    matches = _TRIPLE.findall(text)
    return matches[-1].upper() if matches else None


# --------------------------------------------------------------------- #
# Tier 1 — Classifier                                                   #
# --------------------------------------------------------------------- #
def classify(
    llm: LLM,
    review: SystematicReview,
    candidate: Candidate,
) -> Tuple[str, ClassifierLabel]:
    prompt = prompts.CLASSIFIER.format(
        sr_title=review.title,
        sr_abstract=review.abstract,
        candidate_title=candidate.title,
        candidate_abstract=candidate.abstract,
    )
    return _call_with_label(
        llm,
        settings.worker_model,
        prompt,
        {
            "XXX": ClassifierLabel.POTENTIALLY_RELEVANT,
            "YYY": ClassifierLabel.UNCERTAIN,
            "ZZZ": ClassifierLabel.LIKELY_IRRELEVANT,
        },
        stage="classifier",
    )


# --------------------------------------------------------------------- #
# Tier 2 — Detailed (PICOS) Screener                                    #
# --------------------------------------------------------------------- #
def screen(
    llm: LLM,
    review: SystematicReview,
    candidate: Candidate,
) -> Tuple[str, ScreeningLabel]:
    if not review.objective or not review.method:
        raise ValueError(
            "Detailed screening needs `objective` and `method` on the "
            "SystematicReview — those fields feed the PICOS prompt."
        )
    prompt = prompts.DETAILED_SCREENER.format(
        sr_title=review.title,
        sr_abstract=review.abstract,
        sr_objective=review.objective,
        sr_method=review.method,
        candidate_title=candidate.title,
        candidate_abstract=candidate.abstract,
    )
    return _call_with_label(
        llm,
        settings.worker_model,
        prompt,
        {"XXX": ScreeningLabel.EXCLUDED, "YYY": ScreeningLabel.INCLUDED},
        stage="detailed_screener",
    )


# --------------------------------------------------------------------- #
# Reviewer (LLM-as-a-judge)                                             #
# --------------------------------------------------------------------- #
def review_classification(
    llm: LLM,
    review: SystematicReview,
    candidate: Candidate,
    *,
    justification: str,
    decision: ClassifierLabel,
) -> Tuple[str, bool]:
    prompt = prompts.CLASSIFIER_REVIEWER.format(
        sr_title=review.title,
        sr_abstract=review.abstract,
        candidate_title=candidate.title,
        candidate_abstract=candidate.abstract,
        decision=decision.value.replace("_", " "),
        justification=justification,
    )
    return _review(llm, prompt, stage="classifier_reviewer")


def review_screening(
    llm: LLM,
    review: SystematicReview,
    candidate: Candidate,
    *,
    justification: str,
    decision: ScreeningLabel,
) -> Tuple[str, bool]:
    prompt = prompts.DETAILED_SCREENER_REVIEWER.format(
        sr_title=review.title,
        sr_abstract=review.abstract,
        sr_objective=review.objective,
        sr_method=review.method,
        candidate_title=candidate.title,
        candidate_abstract=candidate.abstract,
        decision=decision.value,
        justification=justification,
    )
    return _review(llm, prompt, stage="detailed_screener_reviewer")


# --------------------------------------------------------------------- #
# Improver (self-correction)                                            #
# --------------------------------------------------------------------- #
def improve_classification(
    llm: LLM,
    review: SystematicReview,
    candidate: Candidate,
    *,
    reviewer_feedback: str,
) -> Tuple[str, ClassifierLabel]:
    original = prompts.CLASSIFIER.format(
        sr_title=review.title,
        sr_abstract=review.abstract,
        candidate_title=candidate.title,
        candidate_abstract=candidate.abstract,
    )
    prompt = prompts.CLASSIFIER_IMPROVER.format(
        original_prompt=original,
        reviewer_feedback=reviewer_feedback,
    )
    return _call_with_label(
        llm,
        settings.worker_model,
        prompt,
        {
            "XXX": ClassifierLabel.POTENTIALLY_RELEVANT,
            "YYY": ClassifierLabel.UNCERTAIN,
            "ZZZ": ClassifierLabel.LIKELY_IRRELEVANT,
        },
        stage="classifier_improver",
        system=prompts.SYSTEM_MESSAGE,
    )


def improve_screening(
    llm: LLM,
    review: SystematicReview,
    candidate: Candidate,
    *,
    reviewer_feedback: str,
) -> Tuple[str, ScreeningLabel]:
    original = prompts.DETAILED_SCREENER.format(
        sr_title=review.title,
        sr_abstract=review.abstract,
        sr_objective=review.objective,
        sr_method=review.method,
        candidate_title=candidate.title,
        candidate_abstract=candidate.abstract,
    )
    prompt = prompts.DETAILED_SCREENER_IMPROVER.format(
        original_prompt=original,
        reviewer_feedback=reviewer_feedback,
    )
    return _call_with_label(
        llm,
        settings.worker_model,
        prompt,
        {"XXX": ScreeningLabel.EXCLUDED, "YYY": ScreeningLabel.INCLUDED},
        stage="detailed_screener_improver",
        system=prompts.SYSTEM_MESSAGE,
    )


# --------------------------------------------------------------------- #
# Internals                                                             #
# --------------------------------------------------------------------- #
def _call_with_label(
    llm: LLM,
    model: str,
    prompt: str,
    marker_to_label: dict,
    *,
    stage: str,
    system: str | None = None,
):
    """Call the model and re-prompt up to `max_retries` times until we see a marker."""
    for attempt in range(1, settings.max_retries + 1):
        result = llm.complete(model=model, user=prompt, system=system)
        marker = _extract_marker(result.text)
        if marker and marker in marker_to_label:
            logger.debug("%s returned %s on attempt %d", stage, marker, attempt)
            return result.text, marker_to_label[marker]
        logger.warning(
            "%s produced no valid sentinel (attempt %d/%d)",
            stage,
            attempt,
            settings.max_retries,
        )

    raise RuntimeError(
        f"{stage} did not emit a valid decision marker after "
        f"{settings.max_retries} attempts."
    )


def _review(llm: LLM, prompt: str, *, stage: str) -> Tuple[str, bool]:
    # The reviewer answers XXX (agree) / YYY (disagree).
    marker_to_bool = {"XXX": True, "YYY": False}
    for attempt in range(1, settings.max_retries + 1):
        result = llm.complete(model=settings.reviewer_model, user=prompt)
        marker = _extract_marker(result.text)
        if marker in marker_to_bool:
            return result.text, marker_to_bool[marker]
        logger.warning(
            "%s produced no valid sentinel (attempt %d/%d)",
            stage,
            attempt,
            settings.max_retries,
        )
    raise RuntimeError(
        f"{stage} did not emit a valid agreement marker after "
        f"{settings.max_retries} attempts."
    )

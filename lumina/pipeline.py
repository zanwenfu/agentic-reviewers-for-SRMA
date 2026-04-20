"""End-to-end LUMINA pipeline.

A candidate is fed through the two-tier loop exactly as described in the
manuscript:

    classifier ──► reviewer ──► improver? ─┐
                       └── include? ──► detailed screener ──► reviewer ──► improver?
                                                                       └──► INCLUDED / EXCLUDED

The pipeline returns a structured `AgentTrace` per candidate so every decision
is fully replayable.
"""
from __future__ import annotations

import logging
from typing import Iterable, Iterator

from . import agents
from .config import settings
from .llm import LLM
from .types import (
    AgentTrace,
    Candidate,
    ClassifierLabel,
    ScreeningLabel,
    SystematicReview,
)

logger = logging.getLogger(__name__)


class ScreeningPipeline:
    """Stateless orchestrator over a shared `LLM` instance."""

    def __init__(self, llm: LLM | None = None) -> None:
        self.llm = llm or LLM()

    # ----------------------------- public API -----------------------------
    def run_one(self, review: SystematicReview, candidate: Candidate) -> AgentTrace:
        """Screen a single candidate end-to-end."""
        trace = AgentTrace(candidate=candidate)
        start_cost = self.llm.total_cost_usd

        # Tier 1: classifier + reviewer loop
        classifier_text, classifier_label = self._classify_with_review(
            review, candidate, trace
        )
        trace.classifier_text = classifier_text
        trace.classifier_label = classifier_label

        if classifier_label is ClassifierLabel.LIKELY_IRRELEVANT:
            trace.final_decision = ScreeningLabel.EXCLUDED
            trace.cost_usd = self.llm.total_cost_usd - start_cost
            return trace

        # Tier 2: detailed screener + reviewer loop
        screener_text, screener_label = self._screen_with_review(
            review, candidate, trace
        )
        trace.screener_text = screener_text
        trace.screener_label = screener_label
        trace.final_decision = screener_label
        trace.cost_usd = self.llm.total_cost_usd - start_cost
        return trace

    def run(
        self,
        review: SystematicReview,
        candidates: Iterable[Candidate],
    ) -> Iterator[AgentTrace]:
        """Screen many candidates, yielding traces as they complete."""
        for candidate in candidates:
            try:
                yield self.run_one(review, candidate)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Screening failed for candidate %r; skipping.", candidate.source_id
                )

    # ----------------------------- internals ------------------------------
    def _classify_with_review(
        self,
        review: SystematicReview,
        candidate: Candidate,
        trace: AgentTrace,
    ):
        justification, label = agents.classify(self.llm, review, candidate)

        for _ in range(settings.max_review_iterations):
            reviewer_text, agreed = agents.review_classification(
                self.llm, review, candidate,
                justification=justification,
                decision=label,
            )
            if agreed:
                trace.record_review(
                    stage="classifier",
                    reviewer_text=reviewer_text,
                    agreed=True,
                )
                return justification, label

            justification, label = agents.improve_classification(
                self.llm, review, candidate, reviewer_feedback=reviewer_text
            )
            trace.record_review(
                stage="classifier",
                reviewer_text=reviewer_text,
                agreed=False,
                improver_text=justification,
            )

        # Fell out of the loop — we accept the last improver output.
        logger.warning(
            "Classifier review loop hit max_review_iterations=%d",
            settings.max_review_iterations,
        )
        return justification, label

    def _screen_with_review(
        self,
        review: SystematicReview,
        candidate: Candidate,
        trace: AgentTrace,
    ):
        justification, label = agents.screen(self.llm, review, candidate)

        for _ in range(settings.max_review_iterations):
            reviewer_text, agreed = agents.review_screening(
                self.llm, review, candidate,
                justification=justification,
                decision=label,
            )
            if agreed:
                trace.record_review(
                    stage="detailed_screener",
                    reviewer_text=reviewer_text,
                    agreed=True,
                )
                return justification, label

            justification, label = agents.improve_screening(
                self.llm, review, candidate, reviewer_feedback=reviewer_text
            )
            trace.record_review(
                stage="detailed_screener",
                reviewer_text=reviewer_text,
                agreed=False,
                improver_text=justification,
            )

        logger.warning(
            "Detailed-screener review loop hit max_review_iterations=%d",
            settings.max_review_iterations,
        )
        return justification, label

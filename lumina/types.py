"""Shared dataclasses flowing between LUMINA agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ClassifierLabel(str, Enum):
    POTENTIALLY_RELEVANT = "potentially_relevant"
    UNCERTAIN = "uncertain"
    LIKELY_IRRELEVANT = "likely_irrelevant"


class ScreeningLabel(str, Enum):
    INCLUDED = "included"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class SystematicReview:
    """The target SRMA whose inclusion criteria we are mirroring."""

    title: str
    abstract: str
    # Objectives and methodology are optional at the classifier tier and
    # required at the detailed-screening tier.
    objective: str = ""
    method: str = ""


@dataclass(frozen=True)
class Candidate:
    """A candidate article to screen."""

    title: str
    abstract: str
    source_id: str = ""  # DOI, PMID, or any upstream identifier


@dataclass
class AgentTrace:
    """Every inference made by every agent for a single candidate.

    Persisting this object is what gives LUMINA its auditability — reviewers
    can replay a decision just by reading the trace.
    """

    candidate: Candidate

    classifier_text: str = ""
    classifier_label: ClassifierLabel | None = None

    screener_text: str = ""
    screener_label: ScreeningLabel | None = None

    review_cycles: list[dict] = field(default_factory=list)
    final_decision: ScreeningLabel | None = None
    cost_usd: float = 0.0

    def record_review(
        self,
        *,
        stage: str,
        reviewer_text: str,
        agreed: bool,
        improver_text: str | None = None,
    ) -> None:
        self.review_cycles.append(
            {
                "stage": stage,
                "reviewer_text": reviewer_text,
                "agreed": agreed,
                "improver_text": improver_text,
            }
        )

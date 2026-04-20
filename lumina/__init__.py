"""LUMINA — an agentic framework for title/abstract screening in SRMAs.

High-level usage:

    from lumina import ScreeningPipeline, SystematicReview, Candidate

    pipeline = ScreeningPipeline()
    trace = pipeline.run_one(
        SystematicReview(title=..., abstract=..., objective=..., method=...),
        Candidate(title=..., abstract=..., source_id="PMID:12345"),
    )
    print(trace.final_decision)
"""
from .pipeline import ScreeningPipeline
from .types import (
    AgentTrace,
    Candidate,
    ClassifierLabel,
    ScreeningLabel,
    SystematicReview,
)

__all__ = [
    "ScreeningPipeline",
    "SystematicReview",
    "Candidate",
    "AgentTrace",
    "ClassifierLabel",
    "ScreeningLabel",
]

__version__ = "0.1.0"

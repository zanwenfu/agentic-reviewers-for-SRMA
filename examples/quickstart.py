"""Screen a handful of candidates end-to-end.

Run:
    cp .env.example .env   # fill in OPENAI_API_KEY
    python examples/quickstart.py
"""
from __future__ import annotations

from lumina import Candidate, ScreeningPipeline, SystematicReview


REVIEW = SystematicReview(
    title=(
        "Gestational diabetes mellitus and development of intergenerational overall "
        "and subtypes of cardiovascular diseases: a systematic review and meta-analysis"
    ),
    abstract=(
        "This systematic review synthesizes evidence on the association between "
        "gestational diabetes mellitus (GDM) and the long-term development of "
        "cardiovascular diseases (CVD) in mothers and offspring post-delivery."
    ),
    objective=(
        "To quantify the association between GDM and subsequent overall and "
        "subtype-specific cardiovascular diseases in both mothers and offspring."
    ),
    method=(
        "Cohort and case-control studies reporting CVD outcomes after a GDM "
        "pregnancy are eligible. Studies without a non-GDM comparator, or "
        "reporting only in-pregnancy outcomes, are excluded."
    ),
)


CANDIDATES = [
    Candidate(
        source_id="PMID:clearly-irrelevant",
        title="Evaluation of fetal myocardial performance index in gestational diabetes mellitus",
        abstract=(
            "We measured fetal myocardial performance index (MPI) in pregnancies "
            "complicated by GDM and compared it to healthy controls. Findings are "
            "restricted to in-utero fetal cardiac function."
        ),
    ),
    Candidate(
        source_id="PMID:clear-include",
        title="Association Between Gestational Diabetes Mellitus and the Risks of Type-Specific Cardiovascular Diseases",
        abstract=(
            "NHANES cohort of women with at least one live birth. Compared to women "
            "without GDM, women with a GDM history had elevated odds of CHD, heart "
            "failure, and stroke, partly mediated by subsequent type 2 diabetes."
        ),
    ),
]


def main() -> None:
    pipeline = ScreeningPipeline()
    for candidate in CANDIDATES:
        trace = pipeline.run_one(REVIEW, candidate)
        print(f"\n=== {candidate.source_id} ===")
        print(f"classifier : {trace.classifier_label.value if trace.classifier_label else '-'}")
        print(f"screener   : {trace.screener_label.value if trace.screener_label else '-'}")
        print(f"final      : {trace.final_decision.value if trace.final_decision else '-'}")
        print(f"review hops: {len(trace.review_cycles)}")
        print(f"cost       : ${trace.cost_usd:.4f}")

    print(f"\nTotal cost for this run: ${pipeline.llm.total_cost_usd:.4f}")


if __name__ == "__main__":
    main()

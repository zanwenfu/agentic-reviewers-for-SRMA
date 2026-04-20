# LUMINA

> **L**arge Language Model **U**nderstanding Systematic Review & **M**eta-Analysis **I**ntegrated **I**n **N**etworked **A**gents

An agentic LLM framework for title/abstract screening in systematic reviews
and meta-analyses (SRMAs). Four small agents — a Classifier, a PICOS
Detailed Screener, a Reviewer (LLM-as-a-judge), and an Improver — cooperate
through a bounded review/improve loop, producing a full written audit trail
for every inclusion decision.

Across 15 published SRMAs, LUMINA reached a mean **sensitivity of 0.982**
(SD 0.027) at **0.879** specificity, with a false-negative rate of **0.018**
— meaning it drops under 2% of the author-included studies on average, and
zero on the median review. On the four benchmark SRMAs from Tran et al.
(*Ann Intern Med*, 2024), it held **perfect (1.000) sensitivity** while
improving specificity by 20–40 points over a GPT-3.5-Turbo PICOS pipeline.
End-to-end cost is **~\$0.07 per 10 candidates**.

The full methodology is in
[`docs/paper/LUMINA_manuscript.pdf`](docs/paper/LUMINA_manuscript.pdf); raw
per-SRMA numbers live in [`docs/paper/supplementary_tables/`](docs/paper/supplementary_tables/);
a one-page results summary is in [`docs/RESULTS.md`](docs/RESULTS.md).

---

## Table of contents

- [Why this exists](#why-this-exists)
- [How it works](#how-it-works)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Reproducing the manuscript results](#reproducing-the-manuscript-results)
- [Repository layout](#repository-layout)
- [Results summary](#results-summary)
- [Limitations & honest caveats](#limitations--honest-caveats)
- [Project history](#project-history)
- [Citation](#citation)

## Why this exists

Manual title/abstract screening is the largest time sink in an SRMA — often
>1,000 hours per review — and single-reviewer pipelines still miss 7–11% of
relevant studies (Gates et al., 2018). Prior LLM approaches mostly fall into
one of two failure modes: high sensitivity with unworkable false-positive
volume, or tight specificity that silently drops true positives.

LUMINA's thesis is small and testable:

1. **Split the decision.** A fast, lenient **classifier** on title+abstract
   alone discards the obviously off-topic tail without losing positives; a
   slower PICOS-structured **detailed screener** makes the final call on
   survivors using the review's objectives and methods as context.
2. **Audit every decision.** A stronger reasoning model acts as a
   **reviewer** (LLM-as-a-judge) over each agent's written justification. If
   it disagrees, an **improver** rewrites the justification using the
   rebuttal; the reviewer re-evaluates until consensus or a cap.
3. **Keep prompts as data.** All six prompt templates live as plain `.txt`
   files in [`lumina/prompts/`](lumina/prompts). The "technique" is small —
   two prompts, plus a judge and a self-correction loop — and the point of
   the repo is that this small technique is enough when composed carefully.

The entire pipeline is ~150 lines of orchestration plus six prompt files.
That is deliberate. If a senior reviewer wants to audit a decision, they
shouldn't need to read a graph library.

## How it works

```
           ┌──────────────┐
           │  Classifier  │  (worker model, e.g. gpt-4o-mini)
           └──────┬───────┘
                  │ justification + {potentially relevant | uncertain | likely irrelevant}
                  ▼
           ┌──────────────┐
           │   Reviewer   │  (reasoning model, e.g. o3-mini)
           └──┬───────┬───┘
     agree   │       │  disagree
             │       ▼
             │   ┌──────────┐
             │   │ Improver │──► loop back to Reviewer
             │   └──────────┘
             ▼
   Likely irrelevant ──────────────────────► EXCLUDED
   Potentially relevant / Uncertain
             │
             ▼
   ┌───────────────────────┐
   │   Detailed Screener   │  PICOS chain-of-thought
   └──────────┬────────────┘
              │
              ▼
     [same Reviewer/Improver loop]
              │
      ┌───────┴────────┐
      ▼                ▼
  INCLUDED         EXCLUDED
```

Design notes live in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
including why the worker and reviewer should be *different* model tiers, and
why the pipeline uses sentinel markers (`XXX`/`YYY`/`ZZZ`) rather than JSON
for decision parsing.

## Quickstart

```bash
git clone https://github.com/<your-handle>/agentic-reviewers-for-SRMA.git
cd agentic-reviewers-for-SRMA
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # and fill in OPENAI_API_KEY
python examples/quickstart.py
```

You should see two candidates screened: one filtered out at the Classifier,
one carried through the Detailed Screener to `INCLUDED`, with the cost and
review-loop depth printed for each.

## Usage

### As a library

```python
from lumina import ScreeningPipeline, SystematicReview, Candidate

review = SystematicReview(
    title="Gestational diabetes mellitus and development of ...",
    abstract="This review synthesizes evidence on ...",
    objective="To quantify the association between GDM and ...",
    method="Cohort and case-control studies reporting CVD ...",
)

pipeline = ScreeningPipeline()
trace = pipeline.run_one(review, Candidate(
    source_id="PMID:12345",
    title="Association Between Gestational Diabetes Mellitus and ...",
    abstract="NHANES cohort of women with at least one live birth ...",
))

print(trace.final_decision)        # ScreeningLabel.INCLUDED
print(trace.classifier_text)       # full CoT from tier 1
print(trace.screener_text)         # full PICOS walkthrough from tier 2
print(trace.review_cycles)         # every reviewer/improver hop
print(f"cost: ${trace.cost_usd}")  # per-candidate cost
```

`trace` is a plain dataclass — persist it as JSON/JSONL to get a replayable
record of every decision.

### As a CLI

```bash
lumina screen \
  --review examples/review.json \
  --candidates examples/candidates.csv \
  -o out.jsonl
```

Supported candidate formats: **CSV** (columns: `id`, `title`, `abstract`)
and **RIS** (`TI`/`AB` fields). Output is JSONL, one decision trace per
line.

### Configuration

`LUMINA` reads configuration from environment variables (`.env` is picked up
automatically if `python-dotenv` is installed):

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | Required. |
| `OPENAI_BASE_URL` | — | Optional; for Azure/proxied endpoints. |
| `LUMINA_WORKER_MODEL` | `gpt-4o-mini` | Classifier, Detailed Screener, Improver. |
| `LUMINA_REVIEWER_MODEL` | `o3-mini` | Reviewer (must be a reasoning-tier model for specificity gains to hold). |
| `LUMINA_LOG_LEVEL` | `INFO` | `DEBUG` surfaces the raw CoT per call. |

## Reproducing the manuscript results

The published runs used `gpt-4o-mini` for the Classifier/Screener/Improver
and `o3-mini` for the Reviewer. To reproduce on your own corpus:

1. Export each SRMA's candidate pool to CSV (one row per retrieved citation,
   columns `id, title, abstract`).
2. Write a `review.json` with the SRMA's title, abstract, objective
   paragraph (typically the last paragraph of the Introduction), and
   methodology paragraph (from Methods).
3. Run `lumina screen --review review.json --candidates pool.csv -o out.jsonl`.
4. Compute metrics by passing `(source_id, final_decision)` pairs and the
   ground-truth included-ID set to `lumina.metrics.compute`.

The exact 15-SRMA corpus used in the paper is not redistributable from this
repository because several of the source datasets are behind publisher
paywalls. See the manuscript's Supplementary Table 1 for the complete search
strategies per review.

## Repository layout

```
.
├── lumina/                 ← installable package
│   ├── __init__.py
│   ├── agents.py           ← Classifier, Screener, Reviewer, Improver (pure functions)
│   ├── pipeline.py         ← orchestration loop
│   ├── llm.py              ← OpenAI wrapper + retry + cost tracking
│   ├── types.py            ← SystematicReview, Candidate, AgentTrace
│   ├── metrics.py          ← sensitivity/specificity/FPR/FNR/PPV/NPV
│   ├── io.py               ← CSV + RIS loaders, JSONL writer
│   ├── cli.py              ← `lumina screen …`
│   └── prompts/            ← six .txt templates (edit these to tune behaviour)
├── examples/
│   ├── quickstart.py
│   ├── review.json
│   └── candidates.csv
├── docs/
│   ├── ARCHITECTURE.md     ← design notes
│   ├── RESULTS.md          ← 1-page results summary
│   └── paper/
│       ├── LUMINA_manuscript.pdf
│       ├── LUMINA_annex_case_examples.docx
│       └── supplementary_tables/   ← authoritative per-SRMA results (CSV)
├── archive/                ← original research code, kept verbatim for provenance
├── pyproject.toml
├── requirements.txt
├── CITATION.cff
├── NOTICE                  ← required attribution text
└── LICENSE                 ← CC BY-NC 4.0 (non-commercial; attribution required)
```

## Results summary

**15 published SRMAs** — authoritative numbers from
[`docs/paper/supplementary_tables/lumina_aggregate_metrics.csv`](docs/paper/supplementary_tables/lumina_aggregate_metrics.csv).
Baselines were reimplemented and run on the same 15 reviews.

| Metric                 | **LUMINA (ours)**  | Oami 2024         | Li 2024           | Strachan 2025     |
| ---------------------- | ------------------ | ----------------- | ----------------- | ----------------- |
| Sensitivity (mean, SD) | **0.982 (0.027)**  | 0.850 (0.092)     | 0.370 (0.288)     | 0.579 (0.302)     |
| FNR (mean, SD)         | **0.018 (0.027)**  | 0.169 (0.183)     | 0.630 (0.288)     | 0.421 (0.302)     |
| Specificity (mean, SD) | 0.879 (0.084)      | 0.907 (0.071)     | **0.980 (0.035)** | 0.942 (0.086)     |
| NPV (mean)             | **0.9995**         | 0.997             | 0.982             | 0.988             |

**Tran et al. 2024 benchmark (4 held-out SRMAs)** — LUMINA vs. GPT-3.5-Turbo PICOS pipeline:

| SRMA              | LUMINA sens / spec | Tran 2024 sens / spec |
| ----------------- | ------------------ | --------------------- |
| Sommer 2023 (v1)  | **1.000 / 0.794**  | 0.811 / 0.574         |
| Sommer 2023 (v2)  | **1.000 / 0.840**  | 0.817 / 0.804         |
| Kiesswetter 2023  | **1.000 / 0.952**  | 0.857 / 0.558         |
| Sbidian 2023      | **1.000 / 0.628**  | 0.965 / 0.258         |

The trade-off is deliberate. LUMINA holds sensitivity at the ceiling (mean
FNR **0.018**, zero on the median review) and spends that budget on a
modest FPR increase. For a screening stage where a missed study invalidates
the review and an extra full-text read costs ten minutes, that is the right
direction.

## Limitations & honest caveats

- **Training-data contamination.** All 15 evaluation SRMAs are published
  papers; frontier models may have seen them. This caveat applies to every
  published LLM-screening benchmark and is discussed in the manuscript.
- **Scope.** LUMINA was validated on SRMAs with one exposure and one
  outcome. Network meta-analyses, multi-exposure designs, and qualitative
  syntheses are out of scope for this version.
- **Bounded review loop.** `max_review_iterations` (default 3) stops a
  pathological reviewer/improver deadlock; the last improver output wins
  when the cap is hit.
- **PPV is low by design.** Aggregate PPV of **0.093** reflects the
  deliberately lenient classifier tier. Downstream full-text review is
  still required — LUMINA shrinks the candidate pool, it does not replace
  reviewers.

## Project history

This started as a year-long research project in collaboration with the Yong
Loo Lin School of Medicine at the National University of Singapore, and was
submitted to *NEJM AI* (manuscript ID AI-25-00939). The author and advisor
later parted ways and no further paper submission is planned. The code and
manuscript are released here so the ideas remain reusable under the
attribution terms below.

The code that produced the manuscript results is preserved verbatim under
[`archive/`](archive/). The `lumina/` package is a clean re-structuring of
that research code: same prompts, same sentinel protocol, same
classifier/reviewer/improver/screener topology, but with a package boundary,
a CLI, a JSONL trace format, and testable pure-function agents.

## Citation

Citation is **required** by the license (see below). Any publication,
paper, preprint, blog post, thesis, internal report, or derived artifact
that uses LUMINA — the code, the prompts, or the data in
`docs/paper/supplementary_tables/` — must cite the manuscript:

```bibtex
@unpublished{fu2025lumina,
  title  = {Application of Large Language Machine Learning Model to Enhance
            Screening Accuracy and Efficiency in Systematic Reviews and
            Meta-Analyses},
  author = {Fu, Zanwen and Chen, Muzi and Yang, Qian and Illanes, Sebastian E.
            and Choolani, Mahesh and Xiao, Xiaokui and Li, Ling-Jun},
  year   = {2025},
  note   = {Manuscript (NEJM AI submission ID AI-25-00939).
            See docs/paper/LUMINA_manuscript.pdf in this repository.},
}
```

Zenodo/DOI metadata is mirrored in [`CITATION.cff`](CITATION.cff) for
GitHub's "Cite this repository" button.

## License

**CC BY-NC 4.0** — see [`LICENSE`](LICENSE) for the full text and
[`NOTICE`](NOTICE) for the required attribution block.

TL;DR:

- **Research, teaching, personal use: permitted**, including redistribution
  and modification.
- **Commercial use is not permitted** under this license. For commercial
  licensing, contact the author (see [`CITATION.cff`](CITATION.cff)).
- **Attribution is required** on every redistribution or derivative work:
  credit "Zanwen Fu, LUMINA (2025)" and link back to this repository and
  the manuscript.

# Results

Authoritative numbers below. Raw per-SRMA breakdowns and baseline runs are
checked in as CSVs under
[`paper/supplementary_tables/`](paper/supplementary_tables) so anyone
replicating this work can diff against the original figures.

## LUMINA on 15 SRMAs (main evaluation)

Ground truth is each SRMA's author-included study list. Data source:
[`paper/supplementary_tables/lumina_15_srmas.csv`](paper/supplementary_tables/lumina_15_srmas.csv).

| Metric          | Mean    | SD      | Min    | Median | Max    |
| --------------- | ------- | ------- | ------ | ------ | ------ |
| **Sensitivity** | **0.982** | 0.027 | 0.923  | 1.000  | 1.000  |
| **Specificity** | **0.879** | 0.084 | 0.665  | 0.888  | 0.982  |
| **FPR**         | 0.117   | 0.083  | 0.018  | 0.111  | 0.335  |
| **FNR**         | 0.018   | 0.027  | 0.000  | 0.000  | 0.077  |
| **NPV**         | 0.9995  | 0.0011 | 0.9960 | 1.000  | 1.000  |
| **PPV**         | 0.093   | 0.083  | 0.018  | 0.072  | 0.345  |

Aggregates:
[`paper/supplementary_tables/lumina_aggregate_metrics.csv`](paper/supplementary_tables/lumina_aggregate_metrics.csv).

### Read these numbers as a product trade-off

- The classifier runs lenient by design. PPV is intentionally low (0.093
  mean); specificity is what matters at this stage, and 0.879 is the right
  yardstick.
- The number that actually protects the review is **FNR ≈ 0.018** — LUMINA
  drops <2% of the author-included studies on average, and zero on the
  median SRMA.
- **NPV ≈ 0.9995** means: if LUMINA excludes a paper, there is a <0.05%
  chance that paper was in the original included set. That's the guarantee
  a reviewer actually needs at the pre-full-text stage.

## Head-to-head against baselines (same 15 SRMAs)

Three published LLM-screening methods were reimplemented and run on the
same 15 SRMAs.

| Metric             | **LUMINA (ours)** | Oami et al. 2024 (ChatGPT screening) | Li et al. 2024 | Strachan 2025 |
| ------------------ | ----------------- | ------------------------------------ | -------------- | ------------- |
| Sensitivity (mean) | **0.982**         | 0.850                                | 0.370          | 0.579         |
| FNR (mean)         | **0.018**         | 0.169                                | 0.630          | 0.421         |
| Specificity (mean) | 0.879             | 0.907                                | **0.980**      | 0.942         |
| FPR (mean)         | 0.117             | 0.090                                | **0.020**      | 0.058         |

The direction of the trade-off is the whole point:

- LUMINA is ~2× the sensitivity of the strongest baseline that maximizes
  specificity (Li 2024), at the cost of ~6× higher FPR.
- For a screening stage where a missed study invalidates the review and an
  extra full-text read costs ten minutes, that's the right direction. The
  review team triages what LUMINA includes; they cannot recover what LUMINA
  drops.

Baseline sources:

- [`paper/supplementary_tables/baseline_oami_chatgpt.csv`](paper/supplementary_tables/baseline_oami_chatgpt.csv)
- [`paper/supplementary_tables/baseline_li_2024.csv`](paper/supplementary_tables/baseline_li_2024.csv)
- [`paper/supplementary_tables/baseline_strachan_2025.csv`](paper/supplementary_tables/baseline_strachan_2025.csv)

## Head-to-head against Tran et al. 2024 (4 held-out SRMAs)

Tran et al. (*Ann Intern Med*, 2024) published a GPT-3.5-Turbo PICOS
pipeline and released per-SRMA numbers on four reviews. LUMINA was run on
the same four under identical conditions.

Source:
[`paper/supplementary_tables/vs_tran_2024.csv`](paper/supplementary_tables/vs_tran_2024.csv).

| SRMA                  | Method      | Sensitivity | Specificity | FPR    | FNR    |
| --------------------- | ----------- | ----------- | ----------- | ------ | ------ |
| Sommer 2023 (v1)      | **LUMINA**  | **1.000**   | **0.794**   | 0.206  | 0.000  |
|                       | Tran 2024   | 0.811       | 0.574       | 0.426  | 0.189  |
| Sommer 2023 (v2)      | **LUMINA**  | **1.000**   | **0.840**   | 0.160  | 0.000  |
|                       | Tran 2024   | 0.817       | 0.804       | 0.196  | 0.183  |
| Kiesswetter 2023      | **LUMINA**  | **1.000**   | **0.952**   | 0.048  | 0.000  |
|                       | Tran 2024   | 0.857       | 0.558       | 0.442  | 0.143  |
| Sbidian 2023          | **LUMINA**  | **1.000**   | **0.628**   | 0.372  | 0.000  |
|                       | Tran 2024   | 0.965       | 0.258       | 0.742  | 0.003  |

LUMINA holds perfect sensitivity across all four SRMAs and roughly doubles
specificity on the two hardest reviews (Kiesswetter, Sbidian).

## Cost & throughput

- **~\$0.07 per 10 candidates** screened end-to-end (classifier + detailed
  screener + reviewer/improver loop), using `gpt-4o-mini` as the worker
  model and `o3-mini` as the reviewer.
- **~400 s (≈6.7 min) wall-clock per 10 candidates**, serial. The pipeline
  is embarrassingly parallel at the candidate level, so throughput scales
  linearly with worker concurrency.

## Honest caveats

- **Training-data contamination.** All 15 evaluation SRMAs are published
  papers; frontier models may have seen them during pretraining. This
  caveat applies to every published LLM-screening benchmark; the manuscript
  discusses it explicitly.
- **Scope.** Validated on SRMAs with one exposure and one outcome. Network
  meta-analyses with many arms, multi-exposure designs, and qualitative
  syntheses are out of scope for this version.
- **PPV is low by design.** Aggregate PPV of 0.093 reflects the deliberately
  lenient classifier tier. Downstream full-text review is still required;
  LUMINA shrinks the candidate pool, it does not replace reviewers.
- **Bounded review loop.** `max_review_iterations` (default 3) caps a
  pathological reviewer/improver deadlock; on the cap, the last improver
  output wins.

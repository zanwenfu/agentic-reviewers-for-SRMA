# Architecture

LUMINA is a two-tier screener wrapped in a self-correcting review loop. The
core claim of the project is small and deliberate: **auditability from two
well-shaped prompts beats a single monolithic "please-screen-this" prompt**,
because each decision carries its own written justification and each
justification is independently challenged by a second model.

## Why a pipeline rather than a single prompt

A systematic review's inclusion decision is a *conjunction* of independent
criteria (population, intervention, comparator, outcome, study design). A
single prompt asks the model to do five things and return one answer; the
reasoning it records is almost always a retrospective summary, not a
derivation.

LUMINA splits the conjunction across two tiers:

1. **Classifier (fast, lenient).** Only the review's title and abstract are
   shown. The goal is to throw out the obviously-off-topic long tail cheaply,
   *without* ever losing a true positive. Bias is intentionally toward
   inclusion.
2. **Detailed screener (slow, PICOS-structured).** Only candidates that
   survived tier 1 get the full objective + methodology context, plus a CoT
   walk through Population → Intervention → Comparison → Outcome → Study
   design.

Each tier is then wrapped by:

3. **Reviewer (LLM-as-a-judge).** A different, stronger model (`o3-mini` by
   default) reads the previous agent's justification and either signs off
   (`XXX`) or rejects it (`YYY`).
4. **Improver.** When the reviewer rejects, the worker model re-runs with the
   reviewer's rebuttal appended. Reviewer and improver cycle until agreement
   or until `max_review_iterations` is hit.

## Flow

```
           ┌──────────────┐
           │  Classifier  │  gpt-4o-mini
           └──────┬───────┘
                  │ justification + {PR, UN, LI}
                  ▼
           ┌──────────────┐
           │   Reviewer   │  o3-mini
           └──┬───────┬───┘
     agree   │       │  disagree
             │       ▼
             │   ┌──────────┐
             │   │ Improver │  (loop back to Reviewer)
             │   └──────────┘
             ▼
     Likely irrelevant ──► EXCLUDED
     Potentially relevant / Uncertain ──► Detailed Screener
                                                    │
                                                    ▼
                                             [same review/improve loop]
                                                    │
                                      ┌─────────────┴─────────────┐
                                      ▼                           ▼
                                  INCLUDED                    EXCLUDED
```

## What's actually in the repo

| Module | Responsibility |
| --- | --- |
| `lumina/prompts/*.txt` | All six prompt templates. Plain text so clinicians can edit without Python. |
| `lumina/agents.py` | Pure functions — one per agent role. Strict sentinel parsing. |
| `lumina/pipeline.py` | The orchestration loop in ~150 readable lines. |
| `lumina/llm.py` | OpenAI wrapper with retry and per-call cost accounting. |
| `lumina/types.py` | `SystematicReview`, `Candidate`, `AgentTrace` dataclasses. |
| `lumina/metrics.py` | Sensitivity / specificity / FPR / FNR / PPV / NPV. |
| `lumina/io.py` | CSV and (minimal) RIS candidate loaders; JSONL trace writer. |
| `lumina/cli.py` | `lumina screen --review r.json --candidates c.csv -o out.jsonl`. |

Everything under `archive/` is the original research code kept verbatim for
reproducibility — it is deliberately *not* part of the installable package.

## Design choices worth defending

- **Sentinel markers (`XXX`/`YYY`/`ZZZ`).** Deliberately preserved from the
  research code. They make every parser in the pipeline a 3-branch regex
  instead of a JSON schema negotiation, which is the single largest source of
  reliability problems we saw during the study.
- **Different models for worker vs reviewer.** Same-model review is cheap but
  rubber-stamps. A reasoning-tier model at the judge seat is where the
  specificity gains actually come from.
- **Plain-text prompts as package data.** Prompt engineering is the
  experiment. Checking prompts into a `prompts/` folder, versioned alongside
  code, is how we made changes reproducible across SRMAs.
- **No background agent framework.** The loop is a hundred lines of Python.
  LangChain/AutoGen would have added indirection without removing a single
  line from the critical path.

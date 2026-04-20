"""Small, dependency-free I/O helpers for candidate pools and results."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Iterator

from .types import AgentTrace, Candidate


def load_candidates_csv(path: str | Path) -> Iterator[Candidate]:
    """Read candidates from a CSV with columns `title`, `abstract`, and optional `id`."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield Candidate(
                title=row["title"].strip(),
                abstract=row.get("abstract", "").strip(),
                source_id=row.get("id", ""),
            )


def load_candidates_ris(path: str | Path) -> Iterator[Candidate]:
    """Minimal RIS parser — pulls TI (title) and AB (abstract) pairs.

    Not a full RIS spec implementation; intentionally simple so callers can
    debug a problematic export by reading one function.
    """
    title: list[str] = []
    abstract: list[str] = []
    mode: str | None = None

    def flush() -> Iterator[Candidate]:
        if title and abstract:
            yield Candidate(title=" ".join(title).strip(), abstract=" ".join(abstract).strip())

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("TI  -"):
                yield from flush()
                title, abstract, mode = [line[6:].strip()], [], "T"
            elif line.startswith("AB  -"):
                abstract, mode = [line[6:].strip()], "A"
            elif line.startswith("ER  -"):
                yield from flush()
                title, abstract, mode = [], [], None
            elif line.startswith("  ") and mode == "T":
                title.append(line.strip())
            elif line.startswith("  ") and mode == "A":
                abstract.append(line.strip())
            else:
                mode = None
    yield from flush()


def write_traces_jsonl(traces: Iterable[AgentTrace], path: str | Path) -> int:
    """Persist traces as newline-delimited JSON. Returns the number of rows written."""
    count = 0
    with open(path, "w", encoding="utf-8") as f:
        for tr in traces:
            f.write(
                json.dumps(
                    {
                        "id": tr.candidate.source_id,
                        "title": tr.candidate.title,
                        "classifier_label": (
                            tr.classifier_label.value if tr.classifier_label else None
                        ),
                        "screener_label": (
                            tr.screener_label.value if tr.screener_label else None
                        ),
                        "final_decision": (
                            tr.final_decision.value if tr.final_decision else None
                        ),
                        "classifier_text": tr.classifier_text,
                        "screener_text": tr.screener_text,
                        "review_cycles": tr.review_cycles,
                        "cost_usd": tr.cost_usd,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            count += 1
    return count

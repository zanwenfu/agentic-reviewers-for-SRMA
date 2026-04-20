"""Minimal CLI: `lumina screen --review review.json --candidates cand.csv -o out.jsonl`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ScreeningPipeline, SystematicReview
from .io import load_candidates_csv, load_candidates_ris, write_traces_jsonl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lumina")
    sub = parser.add_subparsers(dest="command", required=True)

    p_screen = sub.add_parser("screen", help="Run the two-tier screening pipeline.")
    p_screen.add_argument(
        "--review",
        required=True,
        type=Path,
        help="JSON file with keys: title, abstract, objective, method.",
    )
    p_screen.add_argument(
        "--candidates",
        required=True,
        type=Path,
        help="Candidate pool — .csv (title, abstract, id) or .ris.",
    )
    p_screen.add_argument(
        "-o", "--output", required=True, type=Path,
        help="JSONL file to write full agent traces to.",
    )

    args = parser.parse_args(argv)
    if args.command == "screen":
        return _run_screen(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _run_screen(args: argparse.Namespace) -> int:
    review_data = json.loads(args.review.read_text(encoding="utf-8"))
    review = SystematicReview(**review_data)

    if args.candidates.suffix.lower() == ".csv":
        candidates = list(load_candidates_csv(args.candidates))
    elif args.candidates.suffix.lower() == ".ris":
        candidates = list(load_candidates_ris(args.candidates))
    else:
        print(
            f"Unsupported candidate file type: {args.candidates.suffix}. Use .csv or .ris.",
            file=sys.stderr,
        )
        return 2

    print(f"Screening {len(candidates)} candidates …", file=sys.stderr)
    pipeline = ScreeningPipeline()
    traces = list(pipeline.run(review, candidates))
    n = write_traces_jsonl(traces, args.output)

    included = sum(1 for t in traces if t.final_decision and t.final_decision.value == "included")
    print(
        f"Wrote {n} traces to {args.output} "
        f"(included={included}, excluded={n - included}, "
        f"total_cost=${pipeline.llm.total_cost_usd:.4f})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

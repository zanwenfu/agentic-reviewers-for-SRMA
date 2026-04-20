"""Screening performance metrics — the same ones reported in the manuscript.

Given a set of candidates, their ground-truth inclusion labels, and the
predictions emitted by LUMINA, produce the confusion matrix plus sensitivity,
specificity, FPR, FNR, PPV, NPV.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .types import ScreeningLabel


@dataclass(frozen=True)
class Metrics:
    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def sensitivity(self) -> float:  # recall
        return _safe_div(self.tp, self.tp + self.fn)

    @property
    def specificity(self) -> float:
        return _safe_div(self.tn, self.tn + self.fp)

    @property
    def fpr(self) -> float:
        return _safe_div(self.fp, self.fp + self.tn)

    @property
    def fnr(self) -> float:
        return _safe_div(self.fn, self.fn + self.tp)

    @property
    def ppv(self) -> float:  # precision
        return _safe_div(self.tp, self.tp + self.fp)

    @property
    def npv(self) -> float:
        return _safe_div(self.tn, self.tn + self.fn)

    def as_dict(self) -> dict:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "fpr": self.fpr,
            "fnr": self.fnr,
            "ppv": self.ppv,
            "npv": self.npv,
        }


def compute(
    predictions: Iterable[tuple[str, ScreeningLabel]],
    ground_truth_included_ids: set[str],
) -> Metrics:
    """Compare (id, predicted_label) pairs against the set of truly-included IDs."""
    tp = fp = tn = fn = 0
    for source_id, predicted in predictions:
        is_included_pred = predicted is ScreeningLabel.INCLUDED
        is_included_true = source_id in ground_truth_included_ids
        if is_included_pred and is_included_true:
            tp += 1
        elif is_included_pred and not is_included_true:
            fp += 1
        elif not is_included_pred and is_included_true:
            fn += 1
        else:
            tn += 1
    return Metrics(tp=tp, fp=fp, tn=tn, fn=fn)


def _safe_div(num: int, den: int) -> float:
    return num / den if den else 0.0

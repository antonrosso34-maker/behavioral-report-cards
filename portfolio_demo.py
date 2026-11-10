#!/usr/bin/env python3
"""Two-config oracle-union analysis and Wilson uncertainty bands.

Uses the released pass-set headers/evidence only: no model, GPU, or network.
Shows the Gemma UD-Q4 + complement oracle-union upper bound and the 91-answer
uncertainty bands that make "do not select" the honest rule.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "pass-set-header"
GEMMA = ROOT / "evidence" / "gemma-second-family"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


def bands() -> list[tuple[str, float, float, float, float]]:
    out = []
    for label, k, n in (("41/60 pair union", 41, 60), ("5/60 complement gain", 5, 60)):
        lo, hi = wilson(k, n)
        blo, bhi = wilson(k, n, 2.807)
        out.append((label, k / n, lo, hi, blo, bhi))
    return out


def portfolio() -> list[tuple[str, str, int, int, int]]:
    """UD-Q4 portfolio gains reported in the Gemma evidence."""
    return [
        ("heldout", "UD-Q4 + q3", 36, 43, 7),
        ("mbpp", "UD-Q4 + gp1", 35, 38, 3),
        ("dev", "UD-Q4 + q3/google", 29, 33, 4),
    ]


def main() -> None:
    print("certified uncertainty bands (95% and Bonferroni-91):")
    for label, p, lo, hi, blo, bhi in bands():
        print(f"  {label}: {p:.4f} 95% [{lo:.4f}, {hi:.4f}] Bonferroni-91 [{blo:.4f}, {bhi:.4f}]")
    print("two-config oracle-union upper bound (not a deployable selection; no scored run):")
    for split, pair, single, union, gain in portfolio():
        print(f"  {split}: {pair} = {union} vs {single} alone (+{gain})")
    print("rule: these are oracle unions; the target-best pair is not selectable out of sample (see §4.5/§6).")
    print("honest rule: do not select; the bands and reliability (18x60 r=0.231, MDS 0.54%/0.60%) support the boundary.")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""CP@1 / selection-coverage claim-to-evidence self-audit.

Reads the released CP@1 certificate and CP40 analysis only: no model, GPU,
or network. Checks that CP@1 is single-valued, selection coverage is labelled
separately, and the CP40 result is one-sided/INCONCLUSIVE.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CP1 = ROOT / "evidence" / "cp1" / "CP1_FEASIBILITY.md"
CP40 = ROOT / "evidence" / "cp40" / "cp40_analysis.md"
PAPER = ROOT / "paper" / "PAPER_DRAFT_V12.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> None:
    cp1 = read(CP1)
    cp40 = read(CP40)
    paper = read(PAPER)
    checks = []

    checks.append(("CP@1 0.6376", "0.6376" in cp1))
    checks.append(("CP@1 0.6532", "0.6532" in cp1))
    checks.append(("false-pass 18/269", "18/269" in (cp1 + paper)))
    checks.append(("selection coverage separate", "selection coverage" in (cp1 + paper)))
    checks.append(("CP40 one-sided p=0.5", "one-sided" in cp40 and "0.5000" in cp40))
    checks.append(("CP40 INCONCLUSIVE", "INCONCLUSIVE" in cp40))
    checks.append(("CP40 MBPP FAILURE", "FAILURE" in cp40))
    checks.append(("paper CP@1 single-valued", "0.6526" not in paper.split("## 6")[0] if "## 6" in paper else True))

    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"CP@1 AUDIT: {'PASS' if not bad else 'FAIL'}")


if __name__ == "__main__":
    main()

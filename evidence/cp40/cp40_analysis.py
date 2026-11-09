#!/usr/bin/env python3
"""Analyze the frozen 40-task CP@1 panel: anchor vs complement union.

Reads the two JSONL arm files, joins by task, and applies the pre-registered
exact one-sided McNemar rule. Analysis-only; no model run.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def mcnemar_one_sided(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(b, n + 1)) / (2 ** n)


def mcnemar_two_sided(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def paired_bootstrap_ci(anchor, comp, tasks, seed=20261109, reps=10000):
    rng = random.Random(seed)
    deltas = []
    n = len(tasks)
    for _ in range(reps):
        sample = [tasks[rng.randrange(n)] for _ in range(n)]
        a = sum(1 for t in sample if anchor[t])
        u = sum(1 for t in sample if anchor[t] or comp[t])
        deltas.append(u - a)
    deltas.sort()
    return deltas[int(0.025 * reps)], deltas[int(0.975 * reps) - 1]


def load_rows(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def summarize(name, anchor, comp, tasks):
    a = {t: bool(anchor[t]["passed"]) for t in tasks}
    c = {t: bool(comp[t]["passed"]) for t in tasks}
    union = {t: a[t] or c[t] for t in tasks}
    n = len(tasks)
    ap = sum(a.values())
    cp = sum(c.values())
    up = sum(union.values())
    b = sum(1 for t in tasks if union[t] and not a[t])
    cc = sum(1 for t in tasks if a[t] and not union[t])
    p_one = mcnemar_one_sided(b, cc)
    p_two = mcnemar_two_sided(b, cc)
    ci_low, ci_high = paired_bootstrap_ci(a, c, tasks)
    delta = up - ap
    if (delta >= 4 and p_one < 0.10) or ci_low > 0:
        decision = "SUCCESS"
    elif delta <= 0:
        decision = "FAILURE"
    else:
        decision = "INCONCLUSIVE"
    return {
        "group": name,
        "n": n,
        "anchor_passes": ap,
        "complement_passes": cp,
        "union_passes": up,
        "delta_union_minus_anchor": delta,
        "b_union_only": b,
        "c_anchor_only": cc,
        "mcnemar_one_sided_p": round(p_one, 6),
        "mcnemar_two_sided_p": round(p_two, 6),
        "paired_bootstrap_ci95_gain": [ci_low, ci_high],
        "decision": decision,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--complement", required=True)
    parser.add_argument("--split-json", default=str(HERE / "cp40_split.json"))
    parser.add_argument("--out-dir", default=str(HERE))
    args = parser.parse_args()

    split = json.loads(Path(args.split_json).read_text(encoding="utf-8"))
    tasks = [t["task_id"] for t in split["tasks"]]
    anchor_rows = load_rows(Path(args.anchor))
    comp_rows = load_rows(Path(args.complement))
    anchor = {r["task_id"]: r for r in anchor_rows}
    comp = {r["task_id"]: r for r in comp_rows}

    missing_a = [t for t in tasks if t not in anchor]
    missing_c = [t for t in tasks if t not in comp]
    status_a = Counter(r.get("status") for r in anchor_rows)
    status_c = Counter(r.get("status") for r in comp_rows)
    errors_a = sum(v for k, v in status_a.items() if str(k).startswith("request_error"))
    errors_c = sum(v for k, v in status_c.items() if str(k).startswith("request_error"))
    invalid = bool(missing_a or missing_c) or errors_a > 0.1 * len(tasks) or errors_c > 0.1 * len(tasks)

    combined = summarize("combined_40", anchor, comp, tasks) if not invalid else None
    he_tasks = [t for t in tasks if anchor[t]["dataset"] == "humaneval"]
    mbpp_tasks = [t for t in tasks if anchor[t]["dataset"] == "mbpp"]
    he = summarize("humaneval_20", anchor, comp, he_tasks) if not invalid else None
    mbpp = summarize("mbpp_20", anchor, comp, mbpp_tasks) if not invalid else None

    out = {
        "panel_id": split.get("panel_id"),
        "split_json": str(args.split_json),
        "panel_40_sha256_newline": split["hashes"]["panel_40_sha256_newline"],
        "anchor_jsonl": str(args.anchor),
        "complement_jsonl": str(args.complement),
        "status_counts": {"anchor": dict(status_a), "complement": dict(status_c)},
        "missing": {"anchor": missing_a, "complement": missing_c},
        "invalid": invalid,
        "combined": combined,
        "humaneval": he,
        "mbpp": mbpp,
        "cp1": {
            "raw_pair_union": round(combined["union_passes"] / combined["n"], 6) if combined else None,
            "global_adjustment": 0.0669,
            "cp1_global": round((combined["union_passes"] / combined["n"]) * (1 - 0.0669), 6) if combined else None,
            "nine_config_sensitivity": 0.0689,
            "cp1_nine": round((combined["union_passes"] / combined["n"]) * (1 - 0.0689), 6) if combined else None,
            "note": "Adjusted CP@1 uses the raw plus-union rate and the global false-pass adjustment; the 09 certificate is the authority for intervals and scope.",
        },
        "decision_rule": split.get("decision_rule"),
        "power_caveat": split.get("power_caveat"),
    }
    out_path = Path(args.out_dir) / "cp40_analysis.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# CP@1 40-task panel — analysis",
        "",
        f"**Panel:** `{split.get('panel_id')}`; 20 HumanEval+ unused + 20 MBPP+ unused.",
        f"**Panel SHA-256:** `{split['hashes']['panel_40_sha256_newline']}`.",
        f"**Invalid:** {invalid} (missing anchor={len(missing_a)}, complement={len(missing_c)}; "
        f"status anchor={dict(status_a)}, complement={dict(status_c)}).",
        "",
        "| Group | n | Anchor | Complement | Union | Δ union−anchor | b | c | one-sided p | two-sided p | 95% gain CI | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in [combined, he, mbpp]:
        if r is None:
            continue
        lines.append(
            f"| {r['group']} | {r['n']} | {r['anchor_passes']} | {r['complement_passes']} | "
            f"{r['union_passes']} | {r['delta_union_minus_anchor']:+d} | {r['b_union_only']} | "
            f"{r['c_anchor_only']} | {r['mcnemar_one_sided_p']:.4f} | {r['mcnemar_two_sided_p']:.4f} | "
            f"[{r['paired_bootstrap_ci95_gain'][0]}, {r['paired_bootstrap_ci95_gain'][1]}] | {r['decision']} |"
        )
    lines += [
        "",
        f"**CP@1:** raw pair union {out['cp1']['raw_pair_union']}; global-adjusted {out['cp1']['cp1_global']}; nine-config sensitivity {out['cp1']['cp1_nine']}.",
        "",
        "**Pre-registered rule:** success if combined union − anchor ≥ +4/40 and exact one-sided "
        "McNemar p<0.10, or the 95% paired-bootstrap CI lower bound >0; failure if union ≤ anchor; "
        "otherwise inconclusive. +2/40 (p=0.25) and +3/40 (p=0.125) are a practical floor, not "
        "significance; +2/40 all-win is inconclusive. HumanEval and MBPP subgroups are descriptive, "
        "not decision-bearing.",
        "",
        f"**Power caveat:** {split.get('power_caveat', '')}",
        "",
        "**Note:** because the union contains the anchor, `c` (anchor-only passes) is 0 by "
        "construction; the test is equivalent to a one-sided sign test on the complement-only "
        "passes.",
    ]
    (Path(args.out_dir) / "cp40_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

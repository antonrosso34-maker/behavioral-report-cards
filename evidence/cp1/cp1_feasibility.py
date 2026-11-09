"""CP@1 feasibility analysis on the 60-task HumanEval heldout set.

Uses the eight saved compressed configs from the verifier retrospective:
visible = base HumanEval tests, hidden = full HumanEval+ tests (`passed` field).
No model, server, lock, GPU, or scored run. Test execution is CPU-only on saved completions.
"""

from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[5]
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verifier_retro as vr  # noqa: E402

from evalplus.data import get_human_eval_plus  # noqa: E402

OUT = Path(__file__).resolve().parent / "cp1_feasibility_results.json"
CONFIGS = ["q3km_code", "q3km_code_kv8", "q4km_code", "q5ks_none", "q8_0_none", "q3km_none", "q4ks_code", "q5km_none"]


def exact_ci(k: int, n: int) -> list[float]:
    if n == 0:
        return [None, None]
    interval = binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    return [float(interval.low), float(interval.high)]


def main() -> None:
    problems = get_human_eval_plus()
    splits = json.loads((ROOT / "harness" / "data" / "splits.json").read_text(encoding="utf-8"))
    held = list(splits["humaneval"]["heldout"])
    completions = vr.load_completions()

    visible: dict[str, dict[str, bool]] = {}
    hidden: dict[str, dict[str, bool]] = {}
    for config in CONFIGS:
        visible[config] = {}
        hidden[config] = {}
        for task in held:
            row = completions[config][task]
            ok, _ = vr.run_visible(problems[task], row["completion"])
            visible[config][task] = bool(ok)
            hidden[config][task] = bool(row.get("passed"))

    # Per-config raw, hidden, false-pass.
    per_config = {}
    total_visible = 0
    total_false = 0
    for config in CONFIGS:
        v = np.array([visible[config][t] for t in held], dtype=bool)
        h = np.array([hidden[config][t] for t in held], dtype=bool)
        false = int((v & ~h).sum())
        total_visible += int(v.sum())
        total_false += false
        per_config[config] = {
            "visible_pass": int(v.sum()),
            "hidden_pass": int(h.sum()),
            "raw_rate": float(v.mean()),
            "hidden_rate": float(h.mean()),
            "false_pass": false,
            "false_pass_rate_given_visible": float(false / v.sum()) if v.sum() else None,
            "false_pass_ci95": exact_ci(false, int(v.sum())),
            "hidden_given_visible": float((v & h).sum() / v.sum()) if v.sum() else None,
        }

    pooled_false = total_false / total_visible
    pooled_ci = exact_ci(total_false, total_visible)

    # Per-task soundness from the other seven configs (leave-one-config-out).
    loo_cp1 = {}
    for config in CONFIGS:
        weights = []
        for task in held:
            num = 0
            den = 0
            for other in CONFIGS:
                if other == config:
                    continue
                if visible[other][task]:
                    den += 1
                    if hidden[other][task]:
                        num += 1
            weights.append(num / den if den else 1.0)
        weights = np.array(weights, dtype=float)
        v = np.array([visible[config][t] for t in held], dtype=bool)
        loo_cp1[config] = float((v.astype(float) * weights).mean())

    # Global CP@1: raw rate x (1 - pooled false-pass rate) and a conservative lower bound.
    global_cp1 = {c: per_config[c]["raw_rate"] * (1 - pooled_false) for c in CONFIGS}
    global_lb = {c: per_config[c]["raw_rate"] * (1 - pooled_ci[1]) for c in CONFIGS}

    # Rankings.
    raw = np.array([per_config[c]["raw_rate"] for c in CONFIGS])
    hid = np.array([per_config[c]["hidden_rate"] for c in CONFIGS])
    gcp = np.array([global_cp1[c] for c in CONFIGS])
    glb = np.array([global_lb[c] for c in CONFIGS])
    loo = np.array([loo_cp1[c] for c in CONFIGS])

    def corr(a, b):
        s = spearmanr(a, b)
        k = kendalltau(a, b)
        return {"spearman": float(s.statistic), "spearman_p": float(s.pvalue),
                "kendall": float(k.statistic), "kendall_p": float(k.pvalue)}

    def top(values):
        return CONFIGS[int(np.argmax(values))]

    # Per-task LOO contributions: visible pass of this config times the soundness
    # estimated from the other seven configs.
    loo_contrib = {}
    for config in CONFIGS:
        vals = []
        for task in held:
            num = 0
            den = 0
            for other in CONFIGS:
                if other == config:
                    continue
                if visible[other][task]:
                    den += 1
                    if hidden[other][task]:
                        num += 1
            weight = num / den if den else 1.0
            vals.append((1.0 if visible[config][task] else 0.0) * weight)
        loo_contrib[config] = np.array(vals, dtype=float)

    # Bootstrap CP@1 CIs over tasks: raw rate and pooled false-pass resampled together.
    rng = np.random.default_rng(20261109)
    idx = rng.integers(0, len(held), size=(10_000, len(held)))
    boot_global = {c: [] for c in CONFIGS}
    boot_loo = {c: [] for c in CONFIGS}
    for b in range(10_000):
        sample = idx[b]
        # pooled false-pass on the sample across configs
        tv = 0
        tf = 0
        for config in CONFIGS:
            v = np.array([visible[config][t] for t in held], dtype=bool)[sample]
            h = np.array([hidden[config][t] for t in held], dtype=bool)[sample]
            tv += int(v.sum())
            tf += int((v & ~h).sum())
        fp = tf / tv if tv else 0.0
        for config in CONFIGS:
            v = np.array([visible[config][t] for t in held], dtype=bool)[sample]
            boot_global[config].append(float(v.mean() * (1 - fp)))
            boot_loo[config].append(float(loo_contrib[config][sample].mean()))
    for config in CONFIGS:
        per_config[config]["global_cp1"] = global_cp1[config]
        per_config[config]["global_cp1_lb"] = global_lb[config]
        per_config[config]["global_cp1_ci95"] = [
            float(np.percentile(boot_global[config], 2.5)),
            float(np.percentile(boot_global[config], 97.5)),
        ]
        per_config[config]["loo_cp1"] = loo_cp1[config]
        per_config[config]["loo_cp1_ci95"] = [
            float(np.percentile(boot_loo[config], 2.5)),
            float(np.percentile(boot_loo[config], 97.5)),
        ]

    # Private-set high-soundness anchor: 202/202 mutants killed.
    private_ci = exact_ci(202, 202)

    out = {
        "n_tasks": len(held),
        "n_configs": len(CONFIGS),
        "pooled_false_pass": {
            "false": total_false,
            "visible": total_visible,
            "rate": pooled_false,
            "ci95": pooled_ci,
        },
        "private_mutation": {
            "killed": 202,
            "total": 202,
            "score": 1.0,
            "ci95": private_ci,
        },
        "per_config": per_config,
        "rankings": {
            "raw_top": top(raw),
            "hidden_top": top(hid),
            "global_cp1_top": top(gcp),
            "global_lb_top": top(glb),
            "loo_cp1_top": top(loo),
            "raw_vs_hidden": corr(raw, hid),
            "raw_vs_global_cp1": corr(raw, gcp),
            "raw_vs_global_lb": corr(raw, glb),
            "raw_vs_loo_cp1": corr(raw, loo),
            "loo_vs_hidden": corr(loo, hid),
            "global_cp1_vs_hidden": corr(gcp, hid),
        },
        "certificate_40": {
            "expected_false_events_at_6_9pct": 40 * pooled_false,
            "expected_visible_at_50pct": 20,
            "exact_ci_if_3_of_40": exact_ci(3, 40),
            "exact_ci_if_2_of_40": exact_ci(2, 40),
            "note": "A 40-task certificate estimates the global false-pass rate with a wide CI; it cannot separate the per-config false-pass rates (5.3-9.7%) or change the global CP@1 ranking, which is a constant multiple of raw pass@1.",
        },
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    shutil.rmtree(vr.TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

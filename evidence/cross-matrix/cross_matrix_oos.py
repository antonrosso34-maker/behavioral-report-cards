"""Cross-matrix out-of-sample test for the exact-header pair selection.

Select the best pair on the 14x60 heldout matrix (common 12-config set) and
evaluate it on the 12x80 fresh matrix; then reverse. Report selected pairs,
regret, union MAE (rate), top-3, and bootstrap CIs over tasks and configs.

Analysis-only, CPU-only. No scored run, server, lock, GPU, new session, or
commit. Writes only under harness/architect/agents/05_power/.
"""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ARCH = HERE.parents[1]
PAIRED = ARCH / "data" / "paired.csv"
OUT = HERE / "cross_matrix_oos_results.json"

ALPHA = 0.05
SEED = 20261109
B = 2000

HELDOUT_NAMES = [
    "q3km_none_plus", "q4km_code_plus", "q4ks_code_plus", "q3km_code_preplus",
    "q3km_code_kvq8_0_preplus", "q4km_code_preplus", "q3km_code_plus",
    "mx_q3km_code_attnq_q5k_plus", "mx_q3km_code_gateup_q4k_plus",
    "mx2_aq5_q3ks_plus", "mx2_aq6_q3ks_plus", "mx2_aq5_attnk5_plus",
    "mx_q4km_code_attnq_q5k_plus", "q3ks_code_plus",
]
FRESH_NAMES = [
    "mx2_aq5_attnk5_plus", "mx2_aq5_q3ks_plus", "mx2_aq6_q3ks_plus",
    "mx_q3km_code_attnq_q5k_plus", "mx_q3km_code_gateup_q4k_plus",
    "mx_q4km_code_attnq_q5k_plus", "q3km_code_plus", "q3km_code_preplus",
    "q3km_none_plus", "q3ks_code_plus", "q4km_code_plus", "q4ks_code_plus",
]
COMMON = [n for n in HELDOUT_NAMES if n in FRESH_NAMES]


def load_cells():
    rows = [r for r in csv.DictReader(PAIRED.open(encoding="utf-8"))
            if r["family"] == "qwen2.5-coder-1.5b" and r["ref_pass"] != ""]
    by = defaultdict(dict)
    for r in rows:
        by[r["config_name"]][(r["dataset"], r["split"], r["task_id"])] = int(r["passed"])
    return by


def matrix_from(by, names, splits):
    common = set.intersection(*[{t for t in by[c] if (t[0], t[1]) in splits} for c in names])
    tasks = sorted(common)
    M = np.array([[by[c][t] for t in tasks] for c in names], dtype=int)
    return tasks, M


def pair_data(M):
    m, n = M.shape
    iu = np.triu_indices(m, 1)
    u = np.array([np.maximum(M[i], M[j]).sum() for i, j in zip(*iu)], dtype=float)
    return iu, u


def evaluate(source, target, source_names, target_names):
    """Select on source, evaluate on target; both share the same config order."""
    iu_s, us = pair_data(source)
    iu_t, ut = pair_data(target)
    assert source.shape[0] == target.shape[0]
    sel = int(np.argmax(us))
    best_t = int(np.argmax(ut))
    sel_pair = (int(iu_s[0][sel]), int(iu_s[1][sel]))
    best_pair = (int(iu_t[0][best_t]), int(iu_t[1][best_t]))
    regret = float(ut[best_t] - ut[sel])
    mae_rate = float(np.mean(np.abs(us / source.shape[1] - ut / target.shape[1])))
    mae_tasks = float(np.mean(np.abs(us - ut)))
    order = np.argsort(-us)
    top3 = set(order[:3].tolist())
    top3_hit = 1.0 if best_t in top3 else 0.0
    return {
        "selected_pair_idx": sel_pair,
        "selected_pair": [source_names[sel_pair[0]], source_names[sel_pair[1]]],
        "source_union": float(us[sel]),
        "source_best_union": float(us[sel]),
        "target_oracle_idx": best_pair,
        "target_oracle_pair": [target_names[best_pair[0]], target_names[best_pair[1]]],
        "target_oracle_union": float(ut[best_t]),
        "selected_target_union": float(ut[sel]),
        "regret": regret,
        "union_mae_rate": mae_rate,
        "union_mae_tasks_raw": mae_tasks,
        "top3": top3_hit,
        "source_top3": [[int(iu_s[0][k]), int(iu_s[1][k])] for k in order[:3]],
    }


def bootstrap(source, target, mode, rng, b=B):
    """Combined / source-task / target-task / config-only bootstrap."""
    m_s, n_s = source.shape
    m_t, n_t = target.shape
    regs, maes, top3s = [], [], []
    for _ in range(b):
        if mode in ("combined", "config"):
            cfg = np.array(sorted(set(int(x) for x in rng.integers(0, m_s, m_s))))
            if len(cfg) < 2:
                continue
        else:
            cfg = np.arange(m_s)
        if mode in ("combined", "source"):
            s_idx = rng.integers(0, n_s, n_s)
        else:
            s_idx = np.arange(n_s)
        if mode in ("combined", "target"):
            t_idx = rng.integers(0, n_t, n_t)
        else:
            t_idx = np.arange(n_t)
        S = source[np.ix_(cfg, s_idx)]
        T = target[np.ix_(cfg, t_idx)]
        iu_s, us = pair_data(S)
        iu_t, ut = pair_data(T)
        sel = int(np.argmax(us))
        best = int(np.argmax(ut))
        regs.append(float(ut[best] - ut[sel]))
        maes.append(float(np.mean(np.abs(us / n_s - ut / n_t))))
        order = np.argsort(-us)
        top3s.append(1.0 if best in set(order[:3].tolist()) else 0.0)
    return np.array(regs), np.array(maes), np.array(top3s)


def ci(a):
    return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]


def main():
    by = load_cells()
    rng = np.random.default_rng(SEED)
    _, M_h14 = matrix_from(by, HELDOUT_NAMES, {("humaneval", "heldout")})
    _, M_f12 = matrix_from(by, FRESH_NAMES, {("humaneval", "dev"), ("mbpp", "dev")})
    _, M_h = matrix_from(by, COMMON, {("humaneval", "heldout")})
    _, M_f = matrix_from(by, COMMON, {("humaneval", "dev"), ("mbpp", "dev")})
    print("full", M_h14.shape, M_f12.shape, "common", M_h.shape, M_f.shape)

    # Full-matrix best pairs and the missing-config caveat.
    _, u_h14 = pair_data(M_h14)
    iu14 = np.triu_indices(M_h14.shape[0], 1)
    k14 = int(np.argmax(u_h14))
    full14_pair = (HELDOUT_NAMES[iu14[0][k14]], HELDOUT_NAMES[iu14[1][k14]])
    _, u_f12 = pair_data(M_f12)
    iu12 = np.triu_indices(M_f12.shape[0], 1)
    k12 = int(np.argmax(u_f12))
    full12_pair = (FRESH_NAMES[iu12[0][k12]], FRESH_NAMES[iu12[1][k12]])
    missing = [n for n in full14_pair if n not in FRESH_NAMES]

    out = {
        "rule_id": "EXACT-HEADER-CROSS-01",
        "alpha": ALPHA, "seed": SEED, "B": B, "ci_method": "percentile",
        "common_configs": COMMON,
        "full_14x60": {"shape": list(M_h14.shape), "best_pair": list(full14_pair),
                       "best_union": float(u_h14[k14]), "missing_from_12x80": missing},
        "full_12x80": {"shape": list(M_f12.shape), "best_pair": list(full12_pair),
                       "best_union": float(u_f12[k12])},
    }

    for direction, src, tgt, src_names, tgt_names in [
        ("14x60_to_12x80", M_h, M_f, COMMON, COMMON),
        ("12x80_to_14x60", M_f, M_h, COMMON, COMMON),
    ]:
        point = evaluate(src, tgt, src_names, tgt_names)
        boots = {}
        for mode in ("combined", "source", "target", "config"):
            r, a, t = bootstrap(src, tgt, mode, rng)
            boots[mode] = {
                "B": int(len(r)),
                "regret_mean": float(r.mean()), "regret_ci95": ci(r),
                "mae_rate_mean": float(a.mean()), "mae_rate_ci95": ci(a),
                "top3_mean": float(t.mean()), "top3_ci95": ci(t),
            }
        out[direction] = {"point": point, "bootstrap": boots}

    data_hash = hashlib.sha256(PAIRED.read_bytes()).hexdigest()
    cert = {
        "rule_id": out["rule_id"], "version": "1.0", "date": "2026-11-09",
        "alpha": ALPHA, "seed": SEED, "B": B, "ci_method": "percentile",
        "common_configs": COMMON,
        "full_14x60_best_pair": list(full14_pair),
        "full_14x60_missing_from_12x80": missing,
        "scope": "Cross-matrix test on the 12 common configs. The full 14x60 best pair is not evaluable on 12x80 because one config is absent.",
        "data_sha256": data_hash,
    }
    cert["certificate_sha256"] = hashlib.sha256(
        json.dumps(cert, sort_keys=True).encode("utf-8")).hexdigest()
    out["certificate"] = cert
    out["data_sha256"] = data_hash

    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT)
    for d in ("14x60_to_12x80", "12x80_to_14x60"):
        p = out[d]["point"]
        print(f"\n{d}: selected {p['selected_pair']} source_union {p['source_union']} "
              f"target_oracle {p['target_oracle_pair']} {p['target_oracle_union']} "
              f"selected_target {p['selected_target_union']} regret {p['regret']} "
              f"mae_rate {p['union_mae_rate']:.4f} top3 {p['top3']}")
        for mode in ("combined", "source", "target", "config"):
            b = out[d]["bootstrap"][mode]
            print(f"  {mode:8s} regret {b['regret_mean']:.3f} {b['regret_ci95']} "
                  f"mae {b['mae_rate_mean']:.4f} {b['mae_rate_ci95']} "
                  f"top3 {b['top3_mean']:.3f} {b['top3_ci95']}")
    print("\ncertificate", cert["certificate_sha256"])


if __name__ == "__main__":
    main()

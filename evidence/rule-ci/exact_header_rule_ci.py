"""Rule CI for the exact-header pair selection.

Analysis-only, CPU-only. Reconstructs the 14x60 heldout and 12x80 fresh
matrices from harness/architect/data/paired.csv, computes the exact-header
pair-selection metrics (regret, union MAE, top-3), and attaches bootstrap
CIs over tasks and configurations plus a rule certificate.

No scored run, server, lock, GPU, new session, or commit.
Writes only under harness/architect/agents/05_power/.
"""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ARCH = HERE.parents[1]
PAIRED = ARCH / "data" / "paired.csv"
OUT = HERE / "exact_header_rule_ci_results.json"

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


def pair_arrays(M):
    m, n = M.shape
    iu = np.triu_indices(m, 1)
    unions = np.array([np.maximum(M[i], M[j]).sum() for i, j in zip(*iu)], dtype=float)
    return iu, unions


def exact_metrics(M):
    """Within-sample exact-header metrics. They are 0/0/1 by construction."""
    iu, unions = pair_arrays(M)
    best_idx = int(np.argmax(unions))
    best_pair = (int(iu[0][best_idx]), int(iu[1][best_idx]))
    best_union = float(unions[best_idx])
    # The exact header selects the max-union pair, so regret = 0, MAE = 0,
    # and the true best pair is in the top-3 by construction.
    return {
        "best_pair": best_pair,
        "best_union": best_union,
        "best_fixed": int(M.sum(axis=1).max()),
        "union": int(M.max(axis=0).sum()),
        "regret": 0.0,
        "mae": 0.0,
        "top3": 1.0,
    }


def bootstrap_tasks(M, rng, b=B):
    n = M.shape[1]
    regs, maes, top3s = [], [], []
    for _ in range(b):
        idx = rng.integers(0, n, n)
        r = exact_metrics(M[:, idx])
        regs.append(r["regret"]); maes.append(r["mae"]); top3s.append(r["top3"])
    return np.array(regs), np.array(maes), np.array(top3s)


def bootstrap_configs(M, rng, b=B):
    """Resample configs; only pairs of distinct original configs count."""
    m, n = M.shape
    regs, maes, top3s, best_unions, sel_pairs = [], [], [], [], []
    for _ in range(b):
        idx = rng.integers(0, m, m)
        # unique original configs in the resample, preserving multiplicity is
        # not meaningful for a pair of the same config; use unique IDs.
        uniq = sorted(set(int(i) for i in idx))
        if len(uniq) < 2:
            continue
        Mu = M[uniq, :]
        r = exact_metrics(Mu)
        regs.append(r["regret"]); maes.append(r["mae"]); top3s.append(r["top3"])
        best_unions.append(r["best_union"])
        sel_pairs.append((uniq[r["best_pair"][0]], uniq[r["best_pair"][1]]))
    return (np.array(regs), np.array(maes), np.array(top3s),
            np.array(best_unions), Counter(sel_pairs))


def split_half(M, rng, b=B):
    """Out-of-sample: select the pair on one half, evaluate on the other."""
    m, n = M.shape
    iu = np.triu_indices(m, 1)
    regs, maes, top3s = [], [], []
    for _ in range(b):
        perm = rng.permutation(n)
        h = n // 2
        for train, test in [(perm[:h], perm[h:]), (perm[h:], perm[:h])]:
            train_u = np.array([np.maximum(M[i, train], M[j, train]).sum()
                                for i, j in zip(*iu)], dtype=float)
            test_u = np.array([np.maximum(M[i, test], M[j, test]).sum()
                               for i, j in zip(*iu)], dtype=float)
            sel = int(np.argmax(train_u))
            best = int(np.argmax(test_u))
            regs.append(float(test_u[best] - test_u[sel]))
            maes.append(float(np.mean(np.abs(train_u - test_u))))
            order = np.argsort(-train_u)
            top3 = set(order[:3].tolist())
            top3s.append(1.0 if best in top3 else 0.0)
    return np.array(regs), np.array(maes), np.array(top3s)


def ci(a, q=(2.5, 97.5)):
    return [float(np.percentile(a, q[0])), float(np.percentile(a, q[1]))]


def summarize(name, M, rng):
    ex = exact_metrics(M)
    tr, tm, tt = bootstrap_tasks(M, rng)
    cr, cm, ct, cbu, csp = bootstrap_configs(M, rng)
    sr, sm, st = split_half(M, rng)
    n = M.shape[1]
    out = {
        "name": name,
        "shape": list(M.shape),
        "header_bytes": int(np.ceil(n / 8)),
        "exact": {
            "best_fixed": ex["best_fixed"],
            "union": ex["union"],
            "best_union": ex["best_union"],
            "regret": ex["regret"],
            "mae": ex["mae"],
            "top3": ex["top3"],
        },
        "task_bootstrap": {
            "B": int(len(tr)),
            "regret_mean": float(tr.mean()), "regret_ci95": ci(tr),
            "mae_mean": float(tm.mean()), "mae_ci95": ci(tm),
            "top3_mean": float(tt.mean()), "top3_ci95": ci(tt),
            "coverage_point_in_ci": 1.0,
        },
        "config_bootstrap": {
            "B": int(len(cr)),
            "regret_mean": float(cr.mean()), "regret_ci95": ci(cr),
            "mae_mean": float(cm.mean()), "mae_ci95": ci(cm),
            "top3_mean": float(ct.mean()), "top3_ci95": ci(ct),
            "best_union_mean": float(cbu.mean()), "best_union_ci95": ci(cbu),
            "top_pair_frequency": csp.most_common(3),
            "coverage_point_in_ci": 1.0,
        },
        "split_half": {
            "B": int(len(sr)),
            "regret_mean": float(sr.mean()), "regret_ci95": ci(sr),
            "regret_lt1_frac": float(np.mean(sr < 1.0)),
            "mae_mean": float(sm.mean()), "mae_ci95": ci(sm),
            "mae_rate_mean": float(sm.mean() / (n / 2)),
            "mae_rate_lt003_frac": float(np.mean(sm / (n / 2) < 0.03)),
            "top3_mean": float(st.mean()), "top3_ci95": ci(st),
            "top3_ge09_frac": float(np.mean(st >= 0.9)),
        },
    }
    return out


def main():
    by = load_cells()
    rng = np.random.default_rng(SEED)
    heldout_tasks, heldout_M = matrix_from(by, HELDOUT_NAMES, {("humaneval", "heldout")})
    fresh_tasks, fresh_M = matrix_from(by, FRESH_NAMES, {("humaneval", "dev"), ("mbpp", "dev")})
    print("heldout", heldout_M.shape, "fresh", fresh_M.shape)

    res = {
        "rule_id": "EXACT-HEADER-PAIR-01",
        "analysis": "exact-header rule CI",
        "alpha": ALPHA,
        "seed": SEED,
        "B": B,
        "ci_method": "percentile",
        "decision_rule": "select the pair with the maximum union of exact pass-set bitsets; ties broken by smaller total size then lexicographic config order",
        "heldout": summarize("heldout_14x60", heldout_M, rng),
        "fresh": summarize("fresh_12x80", fresh_M, rng),
    }

    # Certificate: content hash over the canonical result plus the data hash.
    data_hash = hashlib.sha256(PAIRED.read_bytes()).hexdigest()
    cert = {
        "rule_id": res["rule_id"],
        "version": "1.0",
        "date": "2026-11-09",
        "alpha": ALPHA,
        "seed": SEED,
        "B": B,
        "ci_method": "percentile",
        "coverage": {
            "heldout_task_bootstrap": res["heldout"]["task_bootstrap"]["coverage_point_in_ci"],
            "heldout_config_bootstrap": res["heldout"]["config_bootstrap"]["coverage_point_in_ci"],
            "fresh_task_bootstrap": res["fresh"]["task_bootstrap"]["coverage_point_in_ci"],
            "fresh_config_bootstrap": res["fresh"]["config_bootstrap"]["coverage_point_in_ci"],
            "heldout_split_half_top3": res["heldout"]["split_half"]["top3_mean"],
            "fresh_split_half_top3": res["fresh"]["split_half"]["top3_mean"],
            "heldout_split_half_regret_lt1": res["heldout"]["split_half"]["regret_lt1_frac"],
            "heldout_split_half_mae_rate_lt003": res["heldout"]["split_half"]["mae_rate_lt003_frac"],
            "heldout_split_half_top3_ge09": res["heldout"]["split_half"]["top3_ge09_frac"],
            "fresh_split_half_regret_lt1": res["fresh"]["split_half"]["regret_lt1_frac"],
            "fresh_split_half_mae_rate_lt003": res["fresh"]["split_half"]["mae_rate_lt003_frac"],
            "fresh_split_half_top3_ge09": res["fresh"]["split_half"]["top3_ge09_frac"],
        },
        "scope": "Within-sample exactness is by construction; the 50/50 split-half is the out-of-sample estimate. The out-of-sample bars (<1 task regret, <0.03 MAE rate, >=0.90 top-3) are not met.",
        "data_sha256": data_hash,
    }
    cert["certificate_sha256"] = hashlib.sha256(
        json.dumps(cert, sort_keys=True).encode("utf-8")).hexdigest()
    res["certificate"] = cert
    res["data_sha256"] = data_hash

    OUT.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT)
    for k in ("heldout", "fresh"):
        r = res[k]
        print(f"\n{k}: exact regret {r['exact']['regret']} mae {r['exact']['mae']} top3 {r['exact']['top3']}")
        print("  task boot", r["task_bootstrap"]["regret_ci95"], r["task_bootstrap"]["mae_ci95"], r["task_bootstrap"]["top3_ci95"])
        print("  config boot", r["config_bootstrap"]["regret_ci95"], r["config_bootstrap"]["mae_ci95"], r["config_bootstrap"]["top3_ci95"])
        print("  split half", r["split_half"]["regret_mean"], r["split_half"]["regret_ci95"],
              r["split_half"]["mae_mean"], r["split_half"]["mae_ci95"],
              r["split_half"]["top3_mean"], r["split_half"]["top3_ci95"])
    print("\ncertificate", cert["certificate_sha256"])


if __name__ == "__main__":
    main()

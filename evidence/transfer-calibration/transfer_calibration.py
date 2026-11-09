"""Transfer-aware / robust pair-selection rules on the 14x60 and 12x80 matrices.

Compares, against the uncalibrated exact-header point-best selection:
  (a) robust: max 10th-percentile union across task bootstraps;
  (b) prior shrinkage: shrink the target estimates toward the other matrix's
      pair performance.

Split-half and cross-matrix regret, union MAE, and top-3. Analysis-only,
CPU-only. No scored run, server, lock, GPU, new session, or commit.
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
OUT = HERE / "transfer_calibration_results.json"

ALPHA = 0.05
SEED = 20261109
B_SPLITS = 500
B_BOOT_SPLIT = 300
B_BOOT_X = 2000
LAMBDAS = [0.25, 0.50, 0.75]

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


def pair_union_matrix(M):
    """Return pair index list and a (n_pairs, n_tasks) union indicator matrix."""
    m, n = M.shape
    iu = np.triu_indices(m, 1)
    U = np.array([np.maximum(M[i], M[j]) for i, j in zip(*iu)], dtype=float)
    return iu, U


def p10_scores(U, other_rate=None, lam=0.0, b_boot=B_BOOT_X, rng=None):
    """10th percentile of the (optionally shrunk) union rate across task bootstraps."""
    n = U.shape[1]
    vals = np.empty((U.shape[0], b_boot), dtype=float)
    for k in range(b_boot):
        idx = rng.integers(0, n, n)
        r = U[:, idx].mean(axis=1)
        if other_rate is not None and lam > 0:
            r = (1.0 - lam) * r + lam * other_rate
        vals[:, k] = r
    return np.percentile(vals, 10, axis=1)


def evaluate(U_train, U_test, scores, other_rate=None, lam=0.0):
    train_rate = U_train.mean(axis=1)
    test_rate = U_test.mean(axis=1)
    best = int(np.argmax(test_rate))
    sel = int(np.argmax(scores))
    order = np.argsort(-scores)
    top3 = 1.0 if best in set(order[:3].tolist()) else 0.0
    if other_rate is not None and lam > 0:
        est = (1.0 - lam) * train_rate + lam * other_rate
    else:
        est = train_rate
    return {
        "selected": sel,
        "regret": float(test_rate[best] - test_rate[sel]),
        "selected_test_rate": float(test_rate[sel]),
        "best_test_rate": float(test_rate[best]),
        "top3": top3,
        "mae_selected": float(abs(est[sel] - test_rate[sel])),
        "mae_overall": float(np.mean(np.abs(est - test_rate))),
    }


def summarize(rows, key):
    a = np.array([r[key] for r in rows], dtype=float)
    return {"mean": float(a.mean()),
            "ci95": [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]}


def split_half_compare(U, other_rate, rng, name):
    n = U.shape[1]
    rules = ["baseline", "robust"] + [f"prior_{int(100*l)}" for l in LAMBDAS] + \
            [f"robust_prior_{int(100*l)}" for l in LAMBDAS]
    rows = {r: [] for r in rules}
    for _ in range(B_SPLITS):
        perm = rng.permutation(n)
        h = n // 2
        train, test = perm[:h], perm[h:]
        Ut, Ue = U[:, train], U[:, test]
        train_rate = Ut.mean(axis=1)
        base_scores = train_rate
        robust_scores = p10_scores(Ut, b_boot=B_BOOT_SPLIT, rng=rng)
        for r, scores, other, lam in [("baseline", base_scores, None, 0.0),
                                      ("robust", robust_scores, None, 0.0)]:
            rows[r].append(evaluate(Ut, Ue, scores, other, lam))
        for lam in LAMBDAS:
            prior_scores = (1 - lam) * train_rate + lam * other_rate
            rows[f"prior_{int(100*lam)}"].append(
                evaluate(Ut, Ue, prior_scores, other_rate, lam))
            rp_scores = p10_scores(Ut, other_rate=other_rate, lam=lam,
                                   b_boot=B_BOOT_SPLIT, rng=rng)
            rows[f"robust_prior_{int(100*lam)}"].append(
                evaluate(Ut, Ue, rp_scores, other_rate, lam))
    out = {"name": name, "splits": B_SPLITS, "boot": B_BOOT_SPLIT, "rules": {}}
    for r in rules:
        out["rules"][r] = {
            "regret": summarize(rows[r], "regret"),
            "selected_test_rate": summarize(rows[r], "selected_test_rate"),
            "top3": summarize(rows[r], "top3"),
            "mae_selected": summarize(rows[r], "mae_selected"),
            "mae_overall": summarize(rows[r], "mae_overall"),
        }
    return out


def cross_compare(U_src, U_tgt, rng, name):
    src_rate = U_src.mean(axis=1)
    tgt_rate = U_tgt.mean(axis=1)
    best = int(np.argmax(tgt_rate))
    robust = p10_scores(U_src, b_boot=B_BOOT_X, rng=rng)
    out = {"name": name, "rules": {}}
    for label, scores in [("baseline", src_rate), ("robust", robust)]:
        sel = int(np.argmax(scores))
        order = np.argsort(-scores)
        out["rules"][label] = {
            "selected": sel,
            "source_rate": float(src_rate[sel]),
            "target_rate": float(tgt_rate[sel]),
            "target_best": float(tgt_rate[best]),
            "regret": float(tgt_rate[best] - tgt_rate[sel]),
            "top3": 1.0 if best in set(order[:3].tolist()) else 0.0,
            "mae_overall": float(np.mean(np.abs(src_rate - tgt_rate))),
        }
    # Prior-shrinkage target selection: target data + source prior (no leakage
    # beyond the observed source matrix; evaluated on the target).
    for lam in LAMBDAS:
        score = (1 - lam) * tgt_rate + lam * src_rate
        sel = int(np.argmax(score))
        order = np.argsort(-score)
        out["rules"][f"prior_target_{int(100*lam)}"] = {
            "selected": sel,
            "target_rate": float(tgt_rate[sel]),
            "target_best": float(tgt_rate[best]),
            "regret": float(tgt_rate[best] - tgt_rate[sel]),
            "top3": 1.0 if best in set(order[:3].tolist()) else 0.0,
            "mae_overall": float(np.mean(np.abs(score - tgt_rate))),
        }
    # target-only baseline for the prior comparison
    score = tgt_rate
    sel = int(np.argmax(score))
    order = np.argsort(-score)
    out["rules"]["target_only"] = {
        "selected": sel,
        "target_rate": float(tgt_rate[sel]),
        "target_best": float(tgt_rate[best]),
        "regret": float(tgt_rate[best] - tgt_rate[sel]),
        "top3": 1.0 if best in set(order[:3].tolist()) else 0.0,
        "mae_overall": 0.0,
    }
    return out


def main():
    by = load_cells()
    rng = np.random.default_rng(SEED)
    _, M_h = matrix_from(by, COMMON, {("humaneval", "heldout")})
    _, M_f = matrix_from(by, COMMON, {("humaneval", "dev"), ("mbpp", "dev")})
    iu, U_h = pair_union_matrix(M_h)
    _, U_f = pair_union_matrix(M_f)
    print("common matrices", M_h.shape, M_f.shape, "pairs", U_h.shape[0])

    rate_h = U_h.mean(axis=1)
    rate_f = U_f.mean(axis=1)

    out = {
        "rule": "TRANSFER-CAL-01",
        "alpha": ALPHA, "seed": SEED,
        "split_half": {
            "14x60": split_half_compare(U_h, rate_f, rng, "14x60"),
            "12x80": split_half_compare(U_f, rate_h, rng, "12x80"),
        },
        "cross": {
            "14x60_to_12x80": cross_compare(U_h, U_f, rng, "14x60_to_12x80"),
            "12x80_to_14x60": cross_compare(U_f, U_h, rng, "12x80_to_14x60"),
        },
    }
    data_hash = hashlib.sha256(PAIRED.read_bytes()).hexdigest()
    out["data_sha256"] = data_hash
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT)

    for m in ("14x60", "12x80"):
        print(f"\nSPLIT-HALF {m}")
        for r, v in out["split_half"][m]["rules"].items():
            print(f"  {r:16s} regret {v['regret']['mean']:.3f} {v['regret']['ci95']} "
                  f"top3 {v['top3']['mean']:.3f} {v['top3']['ci95']} "
                  f"mae_sel {v['mae_selected']['mean']:.4f}")
    for d in ("14x60_to_12x80", "12x80_to_14x60"):
        print(f"\nCROSS {d}")
        for r, v in out["cross"][d]["rules"].items():
            print(f"  {r:18s} regret {v['regret']:.3f} top3 {v['top3']:.1f} "
                  f"target {v['target_rate']:.3f} best {v['target_best']:.3f} "
                  f"mae {v['mae_overall']:.4f}")


if __name__ == "__main__":
    main()

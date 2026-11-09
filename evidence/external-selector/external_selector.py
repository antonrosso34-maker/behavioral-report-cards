#!/usr/bin/env python3
"""External selector baseline: exact header vs sketches vs an L1 logistic selector.

Analysis-only, CPU-only. Uses the 14x60 and 12x80 matrices and public task
features (dataset, reference prompt/completion length bins, task-id bucket,
truncation). The learned selector stores 15 four-bit parameters per config
(7.5 B/config), within the 8 B/10 B exact-header budget.
"""
from __future__ import annotations

import csv
import json
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

import v6_kv8_analysis as v6
import pass_set_sketch as ps

HERE = Path(__file__).resolve().parent
ARCH = HERE.parents[1]
warnings.filterwarnings("ignore")
RNG = np.random.default_rng(20261109)


def load_task_meta():
    meta = {}
    with (ARCH / "data" / "paired.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["family"] != "qwen2.5-coder-1.5b":
                continue
            key = (r["dataset"], r["split"], r["task_id"])
            if key in meta:
                continue
            meta[key] = {
                "prompt": int(r["ref_prompt_tokens"] or 0),
                "completion": int(r["ref_completion_tokens"] or 0),
                "truncated": int(r["ref_truncated"] or 0),
            }
    return meta


def bin_edges(values):
    return np.percentile(np.asarray(values, dtype=float), [25, 50, 75])


def bin_idx(v, edges):
    return int(np.sum(v > edges))


def feature_matrix(tasks, meta, prompt_edges, completion_edges):
    rows = []
    for t in tasks:
        dataset, split, task_id = t
        m = meta[t]
        suffix = int(task_id.split("/")[-1])
        row = [1.0 if dataset == "mbpp" else 0.0]
        p = bin_idx(m["prompt"], prompt_edges)
        c = bin_idx(m["completion"], completion_edges)
        row += [1.0 if p == i else 0.0 for i in range(4)]
        row += [1.0 if c == i else 0.0 for i in range(4)]
        b = suffix % 4
        row += [1.0 if b == i else 0.0 for i in range(4)]
        row += [float(m["truncated"])]
        rows.append(row)
    return np.asarray(rows, dtype=float)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def fit_predict(Xtr, ytr, Xte):
    """L1 logistic with 4-bit weights on a fixed [-4,4] grid (7.5 B/config)."""
    if len(np.unique(ytr)) == 1:
        return np.full(Xte.shape[0], float(ytr[0]))
    clf = LogisticRegression(penalty="l1", solver="liblinear", C=1.0,
                             max_iter=2000, fit_intercept=True)
    clf.fit(Xtr, ytr)
    w = np.concatenate([clf.coef_[0], clf.intercept_])
    q = np.clip(np.round((w + 4.0) / 8.0 * 15.0), 0, 15)
    wq = -4.0 + q / 15.0 * 8.0
    return sigmoid(Xte @ wq[:-1] + wq[-1])


def pair_metrics_from_probs(P, Mte):
    """P: n_test x m predicted pass probabilities; Mte: m x n_test true pass."""
    m, n = Mte.shape
    U_true = np.zeros((m, m), dtype=float)
    U_pred = np.zeros((m, m), dtype=float)
    for a in range(m):
        for b in range(a + 1, m):
            U_true[a, b] = U_true[b, a] = float(np.maximum(Mte[a], Mte[b]).mean())
            U_pred[a, b] = U_pred[b, a] = float(np.mean(P[:, a] + P[:, b] - P[:, a] * P[:, b]))
    iu = np.triu_indices(m, 1)
    true_vals = U_true[iu]
    pred_vals = U_pred[iu]
    best_idx = int(np.argmax(true_vals))
    best_pair = (int(iu[0][best_idx]), int(iu[1][best_idx]))
    sel_idx = int(np.argmax(pred_vals))
    sel_pair = (int(iu[0][sel_idx]), int(iu[1][sel_idx]))
    order = np.argsort(-pred_vals)
    top3 = set(map(tuple, np.array(iu).T[order[:3]].tolist()))
    return {
        "best_pair": best_pair,
        "sel_pair": sel_pair,
        "regret": float((true_vals[best_idx] - true_vals[sel_idx]) * n),
        "mae_rate": float(np.mean(np.abs(pred_vals - true_vals))),
        "mae_tasks": float(np.mean(np.abs(pred_vals - true_vals)) * n),
        "top3": 1.0 if best_pair in top3 else 0.0,
        "cp1": 1.0 if sel_pair == best_pair else 0.0,
        "selected_union_rate": float(true_vals[sel_idx]),
        "oracle_union_rate": float(true_vals[best_idx]),
    }


def exact_select(Mtr, Mte):
    """Exact header: select the pair with the highest training union."""
    m = Mtr.shape[0]
    Utr = np.zeros((m, m))
    Ute = np.zeros((m, m))
    for a in range(m):
        for b in range(a + 1, m):
            Utr[a, b] = Utr[b, a] = float(np.maximum(Mtr[a], Mtr[b]).mean())
            Ute[a, b] = Ute[b, a] = float(np.maximum(Mte[a], Mte[b]).mean())
    iu = np.triu_indices(m, 1)
    tr_vals = Utr[iu]
    te_vals = Ute[iu]
    best_idx = int(np.argmax(te_vals))
    sel_idx = int(np.argmax(tr_vals))
    order = np.argsort(-tr_vals)
    top3 = set(map(tuple, np.array(iu).T[order[:3]].tolist()))
    return {
        "regret": float((te_vals[best_idx] - te_vals[sel_idx]) * Mte.shape[1]),
        "mae_rate": float(np.mean(np.abs(tr_vals - te_vals))),
        "mae_tasks": float(np.mean(np.abs(tr_vals - te_vals)) * Mte.shape[1]),
        "top3": 1.0 if (int(iu[0][best_idx]), int(iu[1][best_idx])) in top3 else 0.0,
        "cp1": 1.0 if sel_idx == best_idx else 0.0,
    }


def summarize(rows):
    out = {}
    for key in ["regret", "mae_tasks", "mae_rate", "top3", "cp1"]:
        vals = np.array([r[key] for r in rows], dtype=float)
        out[key] = {"mean": float(vals.mean()),
                    "p2.5": float(np.percentile(vals, 2.5)),
                    "p97.5": float(np.percentile(vals, 97.5)),
                    "frac": float(np.mean(vals)) if key in ("top3", "cp1") else None}
    return out


def split_half_learned(M, X, reps=200):
    n = M.shape[1]
    m = M.shape[0]
    rows = []
    for _ in range(reps):
        idx = RNG.permutation(n)
        tr, te = idx[: n // 2], idx[n // 2:]
        P = np.column_stack([fit_predict(X[tr], M[c, tr], X[te]) for c in range(m)])
        rows.append(pair_metrics_from_probs(P, M[:, te]))
    return summarize(rows)


def split_half_exact(M, reps=2000):
    n = M.shape[1]
    rows = []
    for _ in range(reps):
        idx = RNG.permutation(n)
        tr, te = idx[: n // 2], idx[n // 2:]
        rows.append(exact_select(M[:, tr], M[:, te]))
    return summarize(rows)


def cross_learned(Msrc, Xsrc, Mtgt, Xtgt):
    m = Msrc.shape[0]
    P = np.column_stack([fit_predict(Xsrc, Msrc[c], Xtgt) for c in range(m)])
    return pair_metrics_from_probs(P, Mtgt)


def cross_exact(Msrc, Mtgt):
    m = Msrc.shape[0]
    Us = np.zeros((m, m))
    Ut = np.zeros((m, m))
    for a in range(m):
        for b in range(a + 1, m):
            Us[a, b] = Us[b, a] = float(np.maximum(Msrc[a], Msrc[b]).mean())
            Ut[a, b] = Ut[b, a] = float(np.maximum(Mtgt[a], Mtgt[b]).mean())
    iu = np.triu_indices(m, 1)
    sv = Us[iu]
    tv = Ut[iu]
    bi = int(np.argmax(tv))
    si = int(np.argmax(sv))
    order = np.argsort(-sv)
    top3 = set(map(tuple, np.array(iu).T[order[:3]].tolist()))
    return {
        "regret": float((tv[bi] - tv[si]) * Mtgt.shape[1]),
        "mae_rate": float(np.mean(np.abs(sv - tv))),
        "mae_tasks": float(np.mean(np.abs(sv - tv)) * Mtgt.shape[1]),
        "top3": 1.0 if (int(iu[0][bi]), int(iu[1][bi])) in top3 else 0.0,
        "cp1": 1.0 if si == bi else 0.0,
    }


def main():
    cells = v6.load_cells()
    meta = load_task_meta()
    tasks14, M14 = v6.matrix_from(cells, v6.NAMES_14, {("humaneval", "heldout")})
    tasks12, M12 = v6.matrix_from(cells, v6.NAMES_12, {("humaneval", "dev"), ("mbpp", "dev")})

    all_tasks = tasks14 + tasks12
    pe = bin_edges([meta[t]["prompt"] for t in all_tasks])
    ce = bin_edges([meta[t]["completion"] for t in all_tasks])
    X14 = feature_matrix(tasks14, meta, pe, ce)
    X12 = feature_matrix(tasks12, meta, pe, ce)
    print(f"14x60: {M14.shape}, features {X14.shape[1]}, 4-bit model {15*4/8:.1f} B/config")
    print(f"12x80: {M12.shape}, features {X12.shape[1]}, 4-bit model {15*4/8:.1f} B/config")

    # Within-sample learned (in-sample; exact header is 0/0/1/1 by construction).
    for label, M, X in (("14x60", M14, X14), ("12x80", M12, X12)):
        P = np.column_stack([fit_predict(X, M[c], X) for c in range(M.shape[0])])
        r = pair_metrics_from_probs(P, M)
        print(f"{label} within-sample learned: regret {r['regret']:.2f}, "
              f"MAE {r['mae_tasks']:.2f} ({r['mae_rate']:.4f}), top3 {r['top3']:.0f}, "
              f"CP@1 {r['cp1']:.0f}")

    sh14e = split_half_exact(M14, reps=2000)
    sh12e = split_half_exact(M12, reps=2000)
    sh14l = split_half_learned(M14, X14, reps=200)
    sh12l = split_half_learned(M12, X12, reps=200)
    print("\nSplit-half exact header:")
    for label, s in (("14x60", sh14e), ("12x80", sh12e)):
        print(f"  {label}: regret {s['regret']['mean']:.2f} "
              f"[{s['regret']['p2.5']:.2f},{s['regret']['p97.5']:.2f}], "
              f"MAE {s['mae_tasks']['mean']:.2f} ({s['mae_rate']['mean']:.4f}), "
              f"top3 {s['top3']['frac']:.3f}, CP@1 {s['cp1']['frac']:.3f}")
    print("Split-half learned L1 logistic (7.5 B/config):")
    for label, s in (("14x60", sh14l), ("12x80", sh12l)):
        print(f"  {label}: regret {s['regret']['mean']:.2f} "
              f"[{s['regret']['p2.5']:.2f},{s['regret']['p97.5']:.2f}], "
              f"MAE {s['mae_tasks']['mean']:.2f} ({s['mae_rate']['mean']:.4f}), "
              f"top3 {s['top3']['frac']:.3f}, CP@1 {s['cp1']['frac']:.3f}")

    print("Split-half sketches (MinHash-512, Bloom-512, random projection):")
    sh_sk = {}
    for method in ("minhash", "bloom", "random"):
        s14 = split_half_sketch(M14, method, 200, seed=100)
        s12 = split_half_sketch(M12, method, 200, seed=200)
        sh_sk[method] = {"14x60": s14, "12x80": s12}
        print(f"  {method:7s} 14x60: regret {s14['regret']['mean']:.2f}, "
              f"MAE {s14['mae_tasks']['mean']:.2f} ({s14['mae_rate']['mean']:.4f}), "
              f"top3 {s14['top3']['frac']:.3f}, CP@1 {s14['cp1']['frac']:.3f}")
        print(f"  {method:7s} 12x80: regret {s12['regret']['mean']:.2f}, "
              f"MAE {s12['mae_tasks']['mean']:.2f} ({s12['mae_rate']['mean']:.4f}), "
              f"top3 {s12['top3']['frac']:.3f}, CP@1 {s12['cp1']['frac']:.3f}")

    M14c = M14[[v6.NAMES_14.index(n) for n in v6.NAMES_12]]
    print("\nCross-matrix (12 common configs):")
    cross_sk = {}
    for src_label, Mtgt, Xtgt, tgt_label in [
        ("14x60", M12, X12, "12x80"),
        ("12x80", M14c, X14, "14x60"),
    ]:
        Msrc, Xsrc = (M14c, X14) if src_label == "14x60" else (M12, X12)
        ce = cross_exact(Msrc, Mtgt)
        cl = cross_learned(Msrc, Xsrc, Mtgt, Xtgt)
        print(f"  {src_label}->{tgt_label} exact: regret {ce['regret']:.0f}, "
              f"MAE {ce['mae_tasks']:.2f} ({ce['mae_rate']:.4f}), top3 {ce['top3']:.0f}, CP@1 {ce['cp1']:.0f}")
        print(f"  {src_label}->{tgt_label} learned: regret {cl['regret']:.0f}, "
              f"MAE {cl['mae_tasks']:.2f} ({cl['mae_rate']:.4f}), top3 {cl['top3']:.0f}, CP@1 {cl['cp1']:.0f}")
        for method in ("minhash", "bloom", "random"):
            cs = cross_sketch(Msrc, Mtgt, method, seed=300)
            cross_sk.setdefault(f"{src_label}->{tgt_label}", {})[method] = cs
            print(f"  {src_label}->{tgt_label} {method:7s}: regret {cs['regret']:.0f}, "
                  f"MAE {cs['mae_tasks']:.2f} ({cs['mae_rate']:.4f}), top3 {cs['top3']:.0f}, CP@1 {cs['cp1']:.0f}")

    out = {
        "features": int(X14.shape[1]),
        "model_bytes_per_config": 15 * 4 / 8,
        "split_half_exact": {"14x60": sh14e, "12x80": sh12e},
        "split_half_learned": {"14x60": sh14l, "12x80": sh12l},
        "split_half_sketch": sh_sk,
        "cross_exact": {},
        "cross_learned": {},
        "cross_sketch": cross_sk,
    }
    for src_label, Mtgt, Xtgt, tgt_label in [
        ("14x60", M12, X12, "12x80"),
        ("12x80", M14c, X14, "14x60"),
    ]:
        Msrc, Xsrc = (M14c, X14) if src_label == "14x60" else (M12, X12)
        out["cross_exact"][f"{src_label}->{tgt_label}"] = cross_exact(Msrc, Mtgt)
        out["cross_learned"][f"{src_label}->{tgt_label}"] = cross_learned(Msrc, Xsrc, Mtgt, Xtgt)
    (HERE / "external_selector_output.json").write_text(json.dumps(out, indent=2) + "\n",
                                                        encoding="utf-8")


def random_projection_unions(M, d, rng):
    n = M.shape[1]
    R = rng.choice(np.array([-1, 1], dtype=np.int8), size=(d, n))
    Y = (R @ M.T).T.astype(np.int32)
    sizes = M.sum(axis=1).astype(float)
    inter = Y @ Y.T
    U = sizes[:, None] + sizes[None, :] - inter
    U = np.clip(U, np.maximum(sizes[:, None], sizes[None, :]), n)
    np.fill_diagonal(U, 0.0)
    return U


def pair_metrics_from_union(U_pred, Mte, n_src=None):
    n_src = n_src or Mte.shape[1]
    n_tgt = Mte.shape[1]
    m = Mte.shape[0]
    U_true = np.zeros((m, m), dtype=float)
    for a in range(m):
        for b in range(a + 1, m):
            U_true[a, b] = U_true[b, a] = float(np.maximum(Mte[a], Mte[b]).sum())
    iu = np.triu_indices(m, 1)
    pred = U_pred[iu] / n_src
    true = U_true[iu] / n_tgt
    bi = int(np.argmax(true))
    si = int(np.argmax(pred))
    order = np.argsort(-pred)
    top3 = set(map(tuple, np.array(iu).T[order[:3]].tolist()))
    return {
        "regret": float((true[bi] - true[si]) * n_tgt),
        "mae_rate": float(np.mean(np.abs(pred - true))),
        "mae_tasks": float(np.mean(np.abs(pred - true)) * n_tgt),
        "top3": 1.0 if (int(iu[0][bi]), int(iu[1][bi])) in top3 else 0.0,
        "cp1": 1.0 if si == bi else 0.0,
    }


def sketch_union(M, method, rng):
    if method == "minhash":
        sig = ps.minhash_signatures(M, 512, rng)
        return ps.minhash_unions(M, sig)
    if method == "bloom":
        return ps.bloom_unions(M, 512, 3, rng)
    d = int(np.ceil(M.shape[1] / 8))
    return random_projection_unions(M, d, rng)


def split_half_sketch(M, method, reps=200, seed=0):
    rng = np.random.default_rng(seed)
    n = M.shape[1]
    rows = []
    for _ in range(reps):
        idx = rng.permutation(n)
        tr, te = idx[: n // 2], idx[n // 2:]
        U = sketch_union(M[:, tr], method, rng)
        rows.append(pair_metrics_from_union(U, M[:, te]))
    return summarize(rows)


def cross_sketch(Msrc, Mtgt, method, seed=0):
    rng = np.random.default_rng(seed)
    U = sketch_union(Msrc, method, rng)
    return pair_metrics_from_union(U, Mtgt, n_src=Msrc.shape[1])


if __name__ == "__main__":
    main()

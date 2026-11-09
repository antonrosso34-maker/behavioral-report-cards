#!/usr/bin/env python3
"""Exact pass-set header evidence: exact bitset vs MinHash-512, Bloom-512,
and a matched-budget random projection.

Analysis-only, CPU-only. Writes only under this directory.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pass_set_sketch as ps  # noqa: E402


def exact_metrics(M):
    m, n = M.shape
    iu = np.triu_indices(m, 1)
    true_vals = np.array([np.maximum(M[i], M[j]).sum() for i, j in zip(*iu)], dtype=float)
    best_idx = int(np.argmax(true_vals))
    best_pair = (int(iu[0][best_idx]), int(iu[1][best_idx]))
    best_union = float(true_vals[best_idx])
    # Exact selection: choose the pair with the highest exact union.
    sel_idx = int(np.argmax(true_vals))
    sel_pair = (int(iu[0][sel_idx]), int(iu[1][sel_idx]))
    sel_union = float(np.maximum(M[sel_pair[0]], M[sel_pair[1]]).sum())
    return {
        "best_pair": best_pair, "best_union": best_union,
        "sel_pair": sel_pair, "sel_union": sel_union,
        "regret": best_union - sel_union,
        "mae": 0.0, "mae_rate": 0.0, "top3": 1.0,
        "bytes": int(np.ceil(n / 8)),
    }


def random_projection_metrics(M, d, rng):
    m, n = M.shape
    R = rng.choice(np.array([-1, 1], dtype=np.int8), size=(d, n))
    Y = (R @ M.T).T.astype(np.int32)  # m x d, entries in [-n, n]
    sizes = M.sum(axis=1).astype(float)
    inter = Y @ Y.T  # m x m
    U = sizes[:, None] + sizes[None, :] - inter
    U = np.clip(U, np.maximum(sizes[:, None], sizes[None, :]), n)
    np.fill_diagonal(U, 0.0)
    return ps.pair_metrics(M, U)


def summarize(method, size_bytes, M, runs):
    regs = np.array([r["regret"] for r in runs], dtype=float)
    maes = np.array([r["mae"] for r in runs], dtype=float)
    top3 = np.array([r["top3"] for r in runs], dtype=float)
    cp1 = np.array([1.0 if r["sel_pair"] == r["best_pair"] else 0.0 for r in runs], dtype=float)
    n = M.shape[1]
    return {
        "method": method,
        "size_bytes": int(size_bytes),
        "regret_mean": float(regs.mean()),
        "regret_p2.5": float(np.percentile(regs, 2.5)),
        "regret_p97.5": float(np.percentile(regs, 97.5)),
        "regret_zero_frac": float(np.mean(regs == 0)),
        "mae_tasks_mean": float(maes.mean()),
        "mae_rate_mean": float(maes.mean() / n),
        "mae_p2.5": float(np.percentile(maes, 2.5)),
        "mae_p97.5": float(np.percentile(maes, 97.5)),
        "mae_bar_frac": float(np.mean(maes / n < 0.03)),
        "top3_frac": float(top3.mean()),
        "cp_at_1_frac": float(cp1.mean()),
        "both_bar_frac": float(np.mean((regs < 1.0) & (maes / n < 0.03))),
    }


def run_matrix(name, names, tasks, M, seeds=200):
    m, n = M.shape
    print(f"\n=== {name}: {m} configs x {n} tasks ===")
    ex = exact_metrics(M)
    print(f"exact header: {ex['bytes']} B/config; best pair {names[ex['best_pair'][0]]} + "
          f"{names[ex['best_pair'][1]]} = {ex['best_union']:.0f}/{n}; "
          f"regret {ex['regret']:.2f}; MAE 0; top3 1.00")
    rows = [{
        "method": "exact_bitset", "size_bytes": ex["bytes"],
        "regret_mean": 0.0, "regret_p2.5": 0.0, "regret_p97.5": 0.0,
        "regret_zero_frac": 1.0, "mae_tasks_mean": 0.0, "mae_rate_mean": 0.0,
        "mae_p2.5": 0.0, "mae_p97.5": 0.0, "mae_bar_frac": 1.0,
        "top3_frac": 1.0, "both_bar_frac": 1.0,
    }]
    # MinHash-512, Bloom-512, MinHash-64, Bloom-64.
    for method, bits in (("minhash", 512), ("bloom", 512), ("minhash", 64), ("bloom", 64)):
        runs = []
        for seed in range(seeds):
            rng = np.random.default_rng(10_000 + seed)
            if method == "minhash":
                sig = ps.minhash_signatures(M, bits, rng)
                U = ps.minhash_unions(M, sig)
            else:
                U = ps.bloom_unions(M, bits, 3, rng)
            runs.append(ps.pair_metrics(M, U))
        size = bits * 4 if method == "minhash" else bits // 8
        row = summarize(f"{method}_{bits}", size, M, runs)
        rows.append(row)
        print(f"{row['method']:14s} {row['size_bytes']:5d} B  regret {row['regret_mean']:.2f} "
              f"[{row['regret_p2.5']:.2f},{row['regret_p97.5']:.2f}] zero {row['regret_zero_frac']:.2f}  "
              f"MAE {row['mae_tasks_mean']:.4f} tasks rate {row['mae_rate_mean']:.4f}  "
              f"top3 {row['top3_frac']:.2f}  cp1 {row['cp_at_1_frac']:.3f}  both {row['both_bar_frac']:.2f}")
    # Random projection at matched budget: d = ceil(n/8) bytes, one int8 per dimension.
    d = int(np.ceil(n / 8))
    runs = []
    for seed in range(seeds):
        rng = np.random.default_rng(20_000 + seed)
        runs.append(random_projection_metrics(M, d, rng))
    row = summarize(f"random_projection_{d}d", d, M, runs)
    rows.append(row)
    print(f"{row['method']:14s} {row['size_bytes']:5d} B  regret {row['regret_mean']:.2f} "
          f"[{row['regret_p2.5']:.2f},{row['regret_p97.5']:.2f}] zero {row['regret_zero_frac']:.2f}  "
          f"MAE {row['mae_tasks_mean']:.4f} tasks rate {row['mae_rate_mean']:.4f}  "
          f"top3 {row['top3_frac']:.2f}  cp1 {row['cp_at_1_frac']:.3f}  both {row['both_bar_frac']:.2f}")
    return rows


def main():
    by, meta = ps.load_cells()
    heldout_names = [
        "q3km_none_plus", "q4km_code_plus", "q4ks_code_plus", "q3km_code_preplus",
        "q3km_code_kvq8_0_preplus", "q4km_code_preplus", "q3km_code_plus",
        "mx_q3km_code_attnq_q5k_plus", "mx_q3km_code_gateup_q4k_plus",
        "mx2_aq5_q3ks_plus", "mx2_aq6_q3ks_plus", "mx2_aq5_attnk5_plus",
        "mx_q4km_code_attnq_q5k_plus", "q3ks_code_plus",
    ]
    tasks, M = ps.matrix_from(by, heldout_names, {("humaneval", "heldout")})
    r1 = run_matrix("heldout_14x60", heldout_names, tasks, M, seeds=200)

    fresh_names = [
        "mx2_aq5_attnk5_plus", "mx2_aq5_q3ks_plus", "mx2_aq6_q3ks_plus",
        "mx_q3km_code_attnq_q5k_plus", "mx_q3km_code_gateup_q4k_plus",
        "mx_q4km_code_attnq_q5k_plus", "q3km_code_plus", "q3km_code_preplus",
        "q3km_none_plus", "q3ks_code_plus", "q4km_code_plus", "q4ks_code_plus",
    ]
    tasks2, M2 = ps.matrix_from(by, fresh_names, {("humaneval", "dev"), ("mbpp", "dev")})
    r2 = run_matrix("fresh_12x80", fresh_names, tasks2, M2, seeds=200)

    out = {
        "heldout": {"n": int(M.shape[1]), "m": int(M.shape[0]), "rows": r1},
        "fresh": {"n": int(M2.shape[1]), "m": int(M2.shape[0]), "rows": r2},
        "metric_note": "both_bar_frac is the regret+MAE bars only; top3_frac and cp_at_1_frac are separate; the all-four intersection is not separately estimated.",
        "notes": "Exact bitset is ceil(n/8) bytes. MinHash sizes assume 32-bit hash values. "
                 "Bloom sizes are bits/8. Random projection uses d=ceil(n/8) int8 dimensions "
                 "(one byte per dimension), matched to the exact header.",
    }
    (HERE / "exact_header_output.json").write_text(json.dumps(out, indent=2) + "\n",
                                                    encoding="utf-8")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Gemma second-family evidence: exact pass-set headers and transfer boundary.

Analysis-only, CPU-only. Reads the Gemma complementarity JSON and the five
configs' JSONLs from the sibling worktree. Writes only under this directory.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PRED = ROOT / "team-predictor-core-8b4a5ef629618ecf" / "harness" / "predictor" / "results" / "gemma_complementarity" / "gemma_complementarity.json"
CONFIGS = ["q3_mix", "google_qat_q4_0", "gp1_qat_requant", "udq4_k_xl", "udq2_k_xl"]
SPLITS = ["he_dev", "he_heldout", "mbpp_heldout"]


def load_split(paths):
    cells = defaultdict(dict)
    for cfg, path in paths.items():
        p = Path(path)
        with p.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tid = r.get("task_id")
                if tid is None:
                    continue
                cells[tid][cfg] = int(bool(r.get("passed")))
    tasks = sorted(t for t, v in cells.items() if all(c in v for c in paths))
    M = np.array([[cells[t][c] for t in tasks] for c in paths], dtype=int)
    return tasks, M


def pair_unions(M):
    m, n = M.shape
    U = np.zeros((m, m), dtype=float)
    for i in range(m):
        for j in range(i + 1, m):
            U[i, j] = U[j, i] = float(np.maximum(M[i], M[j]).sum())
    return U


def pair_list(U):
    m = U.shape[0]
    return [(i, j, U[i, j]) for i in range(m) for j in range(i + 1, m)]


def best_pair(U):
    pairs = pair_list(U)
    i, j, u = max(pairs, key=lambda x: (x[2], -x[0], -x[1]))
    return (i, j), u


def split_half(M, reps=2000, seed=0):
    rng = np.random.default_rng(seed)
    n = M.shape[1]
    m = M.shape[0]
    iu = np.triu_indices(m, 1)
    full_U = pair_unions(M)
    full_best, full_best_u = best_pair(full_U)
    rows = []
    for _ in range(reps):
        idx = rng.permutation(n)
        tr, te = idx[: n // 2], idx[n // 2:]
        Utr = pair_unions(M[:, tr])
        Ute = pair_unions(M[:, te])
        sel, _ = best_pair(Utr)
        sel_test = Ute[sel]
        oracle, oracle_u = best_pair(Ute)
        regret = oracle_u - sel_test
        # Pair-level union-rate prediction error, in test tasks.
        mae_tasks = float(np.mean(np.abs(Utr[iu] / len(tr) - Ute[iu] / len(te))) * len(te))
        # Top-3 by training union; is the test oracle in it?
        order = sorted(pair_list(Utr), key=lambda x: -x[2])
        top3 = {(i, j) for i, j, _ in order[:3]}
        top3_recall = 1.0 if oracle in top3 else 0.0
        cp1 = 1.0 if sel == oracle else 0.0
        rows.append({
            "regret": regret, "mae_tasks": mae_tasks, "mae_rate": mae_tasks / len(te),
            "top3": top3_recall, "cp1": cp1,
            "full_best_selected": 1.0 if sel == full_best else 0.0,
        })
    return rows


def summarize(rows):
    out = {}
    for key in ["regret", "mae_tasks", "mae_rate", "top3", "cp1", "full_best_selected"]:
        vals = np.array([r[key] for r in rows], dtype=float)
        out[key] = {
            "mean": float(vals.mean()),
            "p2.5": float(np.percentile(vals, 2.5)),
            "p97.5": float(np.percentile(vals, 97.5)),
            "frac": float(np.mean(vals)) if key in ("top3", "cp1", "full_best_selected") else None,
        }
    return out


def cross_matrix(src_M, tgt_M, src_name, tgt_name):
    Usrc = pair_unions(src_M)
    Utgt = pair_unions(tgt_M)
    sel, _ = best_pair(Usrc)
    sel_union = Utgt[sel]
    oracle, oracle_u = best_pair(Utgt)
    mae_rate = float(np.mean(np.abs(Usrc[np.triu_indices(Usrc.shape[0], 1)] / src_M.shape[1]
                                   - Utgt[np.triu_indices(Utgt.shape[0], 1)] / tgt_M.shape[1])))
    order = sorted(pair_list(Usrc), key=lambda x: -x[2])
    top3 = {(i, j) for i, j, _ in order[:3]}
    return {
        "source": src_name, "target": tgt_name,
        "selected_pair": sel, "selected_union": float(sel_union),
        "oracle_pair": oracle, "oracle_union": float(oracle_u),
        "regret": float(oracle_u - sel_union),
        "mae_rate": mae_rate,
        "top3": 1.0 if oracle in top3 else 0.0,
        "selected_is_target_best": 1.0 if sel == oracle else 0.0,
    }


def main():
    d = json.loads(PRED.read_text(encoding="utf-8"))
    matrices = {}
    for split in SPLITS:
        paths = {cfg: d["provenance"][cfg]["splits"][split]["path"] for cfg in CONFIGS}
        tasks, M = load_split(paths)
        matrices[split] = (tasks, M)
        expected = [d["splits"][split]["model_pass"][c] for c in CONFIGS]
        actual = [int(M[i].sum()) for i in range(len(CONFIGS))]
        print(f"{split}: n={len(tasks)} shape={M.shape} pass={actual} expected={expected} "
              f"match={actual == expected}")
        ex_best, ex_u = best_pair(pair_unions(M))
        print(f"  exact header {int(np.ceil(len(tasks)/8))} B/config; best pair "
              f"{CONFIGS[ex_best[0]]}+{CONFIGS[ex_best[1]]} = {ex_u:.0f}/{len(tasks)}; "
              f"within-sample regret 0, MAE 0, top3 1.00")
    print("\nSPLIT-HALF (2000 random 50/50 splits):")
    for split in SPLITS:
        tasks, M = matrices[split]
        rows = split_half(M, reps=2000, seed=20261109)
        s = summarize(rows)
        print(f"{split} n={len(tasks)}: regret {s['regret']['mean']:.2f} "
              f"[{s['regret']['p2.5']:.2f},{s['regret']['p97.5']:.2f}], "
              f"MAE {s['mae_tasks']['mean']:.2f} tasks ({s['mae_rate']['mean']:.4f}), "
              f"top3 {s['top3']['frac']:.3f}, CP@1 {s['cp1']['frac']:.3f}, "
              f"full-best selected {s['full_best_selected']['frac']:.3f}")
    print("\nCROSS-MATRIX:")
    rows = []
    for src in SPLITS:
        for tgt in SPLITS:
            if src == tgt:
                continue
            r = cross_matrix(matrices[src][1], matrices[tgt][1], src, tgt)
            rows.append(r)
            print(f"{src}->{tgt}: selected {CONFIGS[r['selected_pair'][0]]}+"
                  f"{CONFIGS[r['selected_pair'][1]]} {r['selected_union']:.0f}/"
                  f"{len(matrices[tgt][0])} vs oracle {r['oracle_union']:.0f}/"
                  f"{len(matrices[tgt][0])} (regret {r['regret']:.0f}, "
                  f"MAE {r['mae_rate']:.4f}, top3 {r['top3']:.0f}, "
                  f"target-best {r['selected_is_target_best']:.0f})")
    out = {
        "configs": CONFIGS,
        "splits": {s: {"n": int(matrices[s][1].shape[1]),
                       "pass": {CONFIGS[i]: int(matrices[s][1][i].sum()) for i in range(len(CONFIGS))},
                       "exact_bytes": int(np.ceil(matrices[s][1].shape[1] / 8))}
                   for s in SPLITS},
        "split_half": {s: summarize(split_half(matrices[s][1], reps=2000, seed=20261109))
                       for s in SPLITS},
        "cross_matrix": rows,
    }
    (HERE / "gemma_second_family_output.json").write_text(json.dumps(out, indent=2) + "\n",
                                                          encoding="utf-8")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""V6 KV8-inclusive 13x80 cross-matrix analysis.

Analysis-only, CPU-only. Uses the existing 14x60 and 12x80 matrices from
paired.csv plus the new KV8 HE-dev/MBPP-dev JSONLs. Writes only under this
directory.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ARCH = HERE.parents[1]
MAIN = Path("C:/Users/Anton/.lmstudio/apps/bionic/projects/d49037d8-47f4-5808-9028-c707de117f8f/workspace/LLM intagration")
KV8_DIR = MAIN / "harness" / "results" / "v6"

NAMES_14 = [
    "q3km_none_plus", "q4km_code_plus", "q4ks_code_plus", "q3km_code_preplus",
    "q3km_code_kvq8_0_preplus", "q4km_code_preplus", "q3km_code_plus",
    "mx_q3km_code_attnq_q5k_plus", "mx_q3km_code_gateup_q4k_plus",
    "mx2_aq5_q3ks_plus", "mx2_aq6_q3ks_plus", "mx2_aq5_attnk5_plus",
    "mx_q4km_code_attnq_q5k_plus", "q3ks_code_plus",
]
NAMES_12 = [
    "mx2_aq5_attnk5_plus", "mx2_aq5_q3ks_plus", "mx2_aq6_q3ks_plus",
    "mx_q3km_code_attnq_q5k_plus", "mx_q3km_code_gateup_q4k_plus",
    "mx_q4km_code_attnq_q5k_plus", "q3km_code_plus", "q3km_code_preplus",
    "q3km_none_plus", "q3ks_code_plus", "q4km_code_plus", "q4ks_code_plus",
]
KV8_NAME = "q3km_code_kvq8_0_preplus"


def load_cells():
    cells = defaultdict(dict)
    with (ARCH / "data" / "paired.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["family"] != "qwen2.5-coder-1.5b" or r["ref_pass"] == "":
                continue
            cells[r["config_name"]][(r["dataset"], r["split"], r["task_id"])] = int(r["passed"])
    return cells


def matrix_from(cells, names, splits):
    common = set.intersection(*[
        {t for t in cells[n] if (t[0], t[1]) in splits} for n in names
    ])
    tasks = sorted(common)
    M = np.array([[cells[n][t] for t in tasks] for n in names], dtype=int)
    return tasks, M


def load_kv8(tasks):
    vals = {}
    for fname in ("v6_kv8_he_dev.jsonl", "v6_kv8_mbpp_dev.jsonl"):
        p = KV8_DIR / fname
        with p.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                vals[(r["dataset"], r["split"], r["task_id"])] = int(bool(r["passed"]))
    return np.array([vals[t] for t in tasks], dtype=int), len(vals)


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
    i, j, u = max(pair_list(U), key=lambda x: (x[2], -x[0], -x[1]))
    return (i, j), u


def split_half(M, reps=2000, seed=20261109):
    rng = np.random.default_rng(seed)
    n = M.shape[1]
    m = M.shape[0]
    iu = np.triu_indices(m, 1)
    full_U = pair_unions(M)
    full_best, _ = best_pair(full_U)
    rows = []
    for _ in range(reps):
        idx = rng.permutation(n)
        tr, te = idx[: n // 2], idx[n // 2:]
        Utr = pair_unions(M[:, tr])
        Ute = pair_unions(M[:, te])
        sel, _ = best_pair(Utr)
        oracle, oracle_u = best_pair(Ute)
        sel_test = Ute[sel]
        mae_tasks = float(np.mean(np.abs(Utr[iu] / len(tr) - Ute[iu] / len(te))) * len(te))
        order = sorted(pair_list(Utr), key=lambda x: -x[2])
        top3 = {(i, j) for i, j, _ in order[:3]}
        rows.append({
            "regret": oracle_u - sel_test,
            "mae_tasks": mae_tasks,
            "mae_rate": mae_tasks / len(te),
            "top3": 1.0 if oracle in top3 else 0.0,
            "cp1": 1.0 if sel == oracle else 0.0,
            "full_best_selected": 1.0 if sel == full_best else 0.0,
        })
    return rows


def summarize(rows):
    out = {}
    for key in ["regret", "mae_tasks", "mae_rate", "top3", "cp1", "full_best_selected"]:
        vals = np.array([r[key] for r in rows], dtype=float)
        out[key] = {"mean": float(vals.mean()),
                    "p2.5": float(np.percentile(vals, 2.5)),
                    "p97.5": float(np.percentile(vals, 97.5)),
                    "frac": float(np.mean(vals)) if key in ("top3", "cp1", "full_best_selected") else None}
    return out


def cross_matrix(src_M, src_names, tgt_M, tgt_names, src_label, tgt_label):
    common = [n for n in src_names if n in tgt_names]
    si = [src_names.index(n) for n in common]
    ti = [tgt_names.index(n) for n in common]
    S = src_M[si]
    T = tgt_M[ti]
    Us = pair_unions(S)
    Ut = pair_unions(T)
    sel, _ = best_pair(Us)
    sel_union = Ut[sel]
    oracle, oracle_u = best_pair(Ut)
    mae_rate = float(np.mean(np.abs(Us[np.triu_indices(len(common), 1)] / S.shape[1]
                                   - Ut[np.triu_indices(len(common), 1)] / T.shape[1])))
    order = sorted(pair_list(Us), key=lambda x: -x[2])
    top3 = {(i, j) for i, j, _ in order[:3]}
    return {
        "source": src_label, "target": tgt_label,
        "common_configs": len(common),
        "selected_pair": (common[sel[0]], common[sel[1]]),
        "selected_union": float(sel_union),
        "selected_rate": float(sel_union / T.shape[1]),
        "oracle_pair": (common[oracle[0]], common[oracle[1]]),
        "oracle_union": float(oracle_u),
        "oracle_rate": float(oracle_u / T.shape[1]),
        "regret": float(oracle_u - sel_union),
        "mae_rate": mae_rate,
        "mae_tasks": mae_rate * T.shape[1],
        "top3": 1.0 if oracle in top3 else 0.0,
        "target_best_selected": 1.0 if sel == oracle else 0.0,
        "source_oracle_pair": (common[best_pair(Us)[0][0]], common[best_pair(Us)[0][1]]),
        "source_oracle_union": float(best_pair(Us)[1]),
        "source_oracle_rate": float(best_pair(Us)[1] / S.shape[1]),
    }


def main():
    cells = load_cells()
    tasks14, M14 = matrix_from(cells, NAMES_14, {("humaneval", "heldout")})
    tasks12, M12 = matrix_from(cells, NAMES_12, {("humaneval", "dev"), ("mbpp", "dev")})
    kv8, n_kv8 = load_kv8(tasks12)
    M13 = np.vstack([M12, kv8[None, :]])
    names13 = NAMES_12 + [KV8_NAME]

    print(f"14x60: {M14.shape}; best fixed {M14.sum(axis=1).max()}/{len(tasks14)}; "
          f"union {M14.max(axis=0).sum()}/{len(tasks14)}")
    print(f"12x80: {M12.shape}; best fixed {M12.sum(axis=1).max()}/{len(tasks12)}; "
          f"union {M12.max(axis=0).sum()}/{len(tasks12)}")
    print(f"KV8: {n_kv8} rows; HE dev {kv8[:40].sum()}/40; MBPP dev {kv8[40:].sum()}/40")
    print(f"13x80: {M13.shape}; best fixed {M13.sum(axis=1).max()}/{len(tasks12)}; "
          f"union {M13.max(axis=0).sum()}/{len(tasks12)}")
    U13 = pair_unions(M13)
    b13, u13 = best_pair(U13)
    print(f"13x80 best pair: {names13[b13[0]]} + {names13[b13[1]]} = {u13:.0f}/{len(tasks12)}")
    print(f"13x80 exact header: 10 B/config; within-sample 0.00 regret, 0.00 MAE, 1.00 top-3")

    # 14x60 full best pair
    b14, u14 = best_pair(pair_unions(M14))
    print(f"14x60 full best pair: {NAMES_14[b14[0]]} + {NAMES_14[b14[1]]} = {u14:.0f}/{len(tasks14)}")

    sh = summarize(split_half(M13, reps=2000, seed=20261109))
    print(f"13x80 split-half: regret {sh['regret']['mean']:.2f} "
          f"[{sh['regret']['p2.5']:.2f},{sh['regret']['p97.5']:.2f}], "
          f"MAE {sh['mae_tasks']['mean']:.2f} tasks ({sh['mae_rate']['mean']:.4f}), "
          f"top3 {sh['top3']['frac']:.3f}, CP@1 {sh['cp1']['frac']:.3f}, "
          f"full-best {sh['full_best_selected']['frac']:.3f}")

    rows = []
    for src_M, src_names, src_label, tgt_M, tgt_names, tgt_label in [
        (M14, NAMES_14, "14x60", M13, names13, "13x80"),
        (M13, names13, "13x80", M14, NAMES_14, "14x60"),
        (M14, NAMES_14, "14x60", M12, NAMES_12, "12x80"),
        (M12, NAMES_12, "12x80", M14, NAMES_14, "14x60"),
    ]:
        r = cross_matrix(src_M, src_names, tgt_M, tgt_names, src_label, tgt_label)
        rows.append(r)
        print(f"{src_label}->{tgt_label} ({r['common_configs']} common): "
              f"selected {r['selected_pair'][0]}+{r['selected_pair'][1]} "
              f"{r['selected_union']:.0f}/{tgt_M.shape[1]} vs oracle "
              f"{r['oracle_union']:.0f}/{tgt_M.shape[1]} (regret {r['regret']:.0f}, "
              f"MAE {r['mae_rate']:.4f}, top3 {r['top3']:.0f}, "
              f"target-best {r['target_best_selected']:.0f})")

    out = {
        "n14": int(M14.shape[1]), "n12": int(M12.shape[1]), "n13": int(M13.shape[1]),
        "kv8_pass": {"he_dev": int(kv8[:40].sum()), "mbpp_dev": int(kv8[40:].sum())},
        "best_fixed_14": int(M14.sum(axis=1).max()),
        "union_14": int(M14.max(axis=0).sum()),
        "best_fixed_12": int(M12.sum(axis=1).max()),
        "union_12": int(M12.max(axis=0).sum()),
        "best_fixed_13": int(M13.sum(axis=1).max()),
        "union_13": int(M13.max(axis=0).sum()),
        "best_pair_13": {"a": names13[b13[0]], "b": names13[b13[1]], "union": float(u13)},
        "best_pair_14": {"a": NAMES_14[b14[0]], "b": NAMES_14[b14[1]], "union": float(u14)},
        "split_half_13": sh,
        "cross": rows,
    }
    (HERE / "v6_kv8_analysis_output.json").write_text(json.dumps(out, indent=2) + "\n",
                                                      encoding="utf-8")


if __name__ == "__main__":
    main()

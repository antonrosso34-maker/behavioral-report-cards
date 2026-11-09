#!/usr/bin/env python3
"""Freeze the 40-task CP@1 panel split (20 HumanEval+ unused + 20 MBPP+ unused).

Analysis-only: reads existing split manifests and writes the frozen split, task IDs,
and canonical hashes. No model run.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # .../harness
DATA = ROOT / "data"
SPLITS = DATA / "splits.json"
STAGE2_MBPP = DATA / "stage2_mbpp.json"
V14 = ROOT / "architect" / "agents" / "01_variance" / "probe02_v14_split.json"
V14_SHA_FILE = V14.with_suffix(".sha256")

SEED = 20261109
MODEL_SHA = {
    "q3km_code_kvq8_0_preplus": "fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb",
    "mx_q4km_code_attnq_q5k_plus": "f03ecc3eeb5f957f1331aae886779730bbaa9f1825d1abd075fa894407760b74",
}


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def merkle_root(ids: list[str]) -> str:
    leaves = [hashlib.sha256(x.encode("utf-8")).digest() for x in ids]
    if not leaves:
        return hashlib.sha256(b"").hexdigest()
    while len(leaves) > 1:
        if len(leaves) % 2:
            leaves.append(leaves[-1])
        leaves = [hashlib.sha256(leaves[i] + leaves[i + 1]).digest()
                  for i in range(0, len(leaves), 2)]
    return leaves[0].hex()


def main():
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    he_pool = sorted(splits["humaneval"]["unused"])
    stage2 = json.loads(STAGE2_MBPP.read_text(encoding="utf-8"))
    parent = sorted(stage2["ids"])
    v14 = json.loads(V14.read_text(encoding="utf-8"))
    v14_ids = set(v14["ids"])
    mbpp_pool = sorted(set(parent) - v14_ids)

    assert len(he_pool) == 64, len(he_pool)
    assert len(parent) == 200, len(parent)
    assert len(v14_ids) == 120, len(v14_ids)
    assert len(mbpp_pool) == 80, len(mbpp_pool)

    rng = random.Random(SEED)
    he_sel = sorted(rng.sample(he_pool, 20))
    mbpp_sel = sorted(rng.sample(mbpp_pool, 20))
    remaining_mbpp = sorted(set(mbpp_pool) - set(mbpp_sel))
    assert len(he_sel) == 20 and len(mbpp_sel) == 20 and len(remaining_mbpp) == 60

    tasks = (
        [{"dataset": "humaneval", "split": "unused", "task_id": t} for t in he_sel]
        + [{"dataset": "mbpp", "split": "unused", "task_id": t} for t in mbpp_sel]
    )

    he_txt = "\n".join(he_sel) + "\n"
    mbpp_txt = "\n".join(mbpp_sel) + "\n"
    all_txt = "\n".join(f"{t['dataset']}/{t['split']}/{t['task_id']}" for t in tasks) + "\n"
    rem_txt = "\n".join(remaining_mbpp) + "\n"

    split = {
        "panel_id": "CP40-V6",
        "created_at": "2026-11-09T20:18:21Z",
        "selection_seed": SEED,
        "selection_rule": (
            "One random.Random(20261109) stream: sample 20 from sorted humaneval.unused (64), "
            "then sample 20 from sorted mbpp.unused minus the probe02_v14 120-task slice (80); "
            "sort each selection. The remaining 60 MBPP+ tasks stay sealed; the 2-task reserve "
            "is untouched."
        ),
        "counts": {"humaneval": 20, "mbpp": 20, "total": 40},
        "tasks": tasks,
        "remaining_sealed": {
            "mbpp": 60,
            "mbpp_ids_sha256_newline": sha_text(rem_txt),
            "humaneval_unused_remaining": 44,
            "reserve": 2,
        },
        "parents": {
            "splits_json_sha256": hashlib.sha256(SPLITS.read_bytes()).hexdigest(),
            "stage2_mbpp_parent_sha256": stage2.get("sha256"),
            "stage2_mbpp_parent_count": len(parent),
            "probe02_v14_slice_sha256": V14_SHA_FILE.read_text(encoding="utf-8").split()[0],
            "probe02_v14_slice_count": len(v14_ids),
        },
        "hashes": {
            "humaneval_20_sha256_newline": sha_text(he_txt),
            "humaneval_20_sha256_json": sha_text(json.dumps(he_sel, separators=(",", ":"))),
            "mbpp_20_sha256_newline": sha_text(mbpp_txt),
            "mbpp_20_sha256_json": sha_text(json.dumps(mbpp_sel, separators=(",", ":"))),
            "panel_40_sha256_newline": sha_text(all_txt),
            "panel_40_sha256_json": sha_text(json.dumps([f"{t['dataset']}/{t['split']}/{t['task_id']}" for t in tasks], separators=(",", ":"))),
            "remaining_mbpp_60_sha256_newline": sha_text(rem_txt),
            "merkle_root": merkle_root([f"{t['dataset']}/{t['split']}/{t['task_id']}" for t in tasks]),
        },
        "models": MODEL_SHA,
        "decision_rule": {
            "primary": "Combined 40 tasks: pair union vs anchor; exact one-sided McNemar.",
            "success": "union - anchor >= +4/40 and exact one-sided McNemar p < 0.10, or 95% paired-bootstrap CI lower > 0.",
            "failure": "union <= anchor.",
            "precision": "+2/40 all-win p=0.25; +3/40 all-win p=0.125; +4/40 all-win p=0.0625. +2 and +3 are a practical floor, not significance; +2 all-win is inconclusive.",
            "inconclusive": "otherwise.",
            "subgroups": "HumanEval 20 and MBPP 20 reported separately; descriptive, not decision-bearing.",
        },
        "power_caveat": (
            "The 14x60 expected gain is +5/60 = +3.3/40; the 40-task exact McNemar is a screen, "
            "not a powered confirmation. The panel is a real-code-benchmark transfer test."
        ),
        "status": "FROZEN; NOT RUN",
    }

    (HERE / "cp40_split.json").write_text(json.dumps(split, indent=2) + "\n", encoding="utf-8")
    (HERE / "cp40_task_ids.txt").write_bytes(all_txt.encode("utf-8"))
    (HERE / "cp40_task_ids.json").write_bytes(
        (json.dumps([f"{t['dataset']}/{t['split']}/{t['task_id']}" for t in tasks], indent=2) + "\n").encode("utf-8")
    )
    (HERE / "cp40_hashes.json").write_text(json.dumps(split["hashes"], indent=2) + "\n", encoding="utf-8")
    merkle = {
        "algorithm": "SHA-256 leaves over dataset/split/task_id; duplicate last leaf on odd count; hex root",
        "n_leaves": len(tasks),
        "root": split["hashes"]["merkle_root"],
        "leaves": [hashlib.sha256(f"{t['dataset']}/{t['split']}/{t['task_id']}".encode()).hexdigest() for t in tasks],
    }
    (HERE / "cp40_merkle.json").write_text(json.dumps(merkle, indent=2) + "\n", encoding="utf-8")
    print("frozen", HERE / "cp40_split.json")
    print("humaneval", len(he_sel), "mbpp", len(mbpp_sel), "remaining mbpp sealed", len(remaining_mbpp))
    print("panel sha", split["hashes"]["panel_40_sha256_newline"])
    print("remaining mbpp sha", split["hashes"]["remaining_mbpp_60_sha256_newline"])


if __name__ == "__main__":
    main()

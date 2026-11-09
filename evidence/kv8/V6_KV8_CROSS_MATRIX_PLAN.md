# V6 KV8-inclusive cross-matrix plan

**Agent:** `04_routing`  
**Date:** 2026-11-09  
**Scope:** Plan and run script only. No scored run, server, lock, GPU, new session, or commit by this agent. The lead launches after the 40-task panel.

## 1. Why KV8 is missing

The current Qwen 12×80 matrix has 12 configurations on HumanEval dev 40 + MBPP dev 40:

`mx2_aq5_attnk5_plus`, `mx2_aq5_q3ks_plus`, `mx2_aq6_q3ks_plus`, `mx_q3km_code_attnq_q5k_plus`, `mx_q3km_code_gateup_q4k_plus`, `mx_q4km_code_attnq_q5k_plus`, `q3km_code_plus`, `q3km_code_preplus`, `q3km_none_plus`, `q3ks_code_plus`, `q4km_code_plus`, `q4ks_code_plus`.

The 14×60 heldout matrix additionally contains `q3km_code_kvq8_0_preplus` (KV8) and `q4km_code_preplus`. KV8 has the 60 heldout tasks and MBPP dev 40, but it has **no HumanEval dev 40**, so it is excluded from the 12×80 matrix. `q4km_code_preplus` has HumanEval dev 40 but no MBPP dev 40, so it is also excluded. The V6 residual test needs KV8 in the target matrix to remove the 12-common-config confound: the full 14×60 oracle is 41/60, while the 12-common-config oracle is 39/60.

## 2. Plan chosen

**Add KV8 to the 12×80 matrix with 80 generations**: 40 HumanEval dev + 40 MBPP dev for `q3km_code` with `kv_cache=q8_0`. This produces a clean **13×80** matrix with a matched protocol. The existing KV8 MBPP dev cells in `paired.csv` are not reused because the V6 matrix should have one protocol and one provenance trail; the 80-generation run is the clean unit the lead asked for.

A full 14×80 matrix would also require 80 generations for `q4km_code_preplus`; that is **not** in this plan. The V6 residual test only needs KV8.

## 3. Split IDs and hashes

Recorded in `harness/architect/agents/04_routing/v6_kv8_split_ids.json`:

| item | n | SHA-256 |
|---|---:|---|
| `harness/data/splits.json` | — | `dd5cd10676843ac3e8ebf2a7ed7190db0421aa3ee1c821ea4009824e8624d12d` |
| HumanEval dev task list | 40 | `e9ae9025a99a5b2a8e5719d39e07cabe81ef659b9bf4a8a572fcbefed5e61280` |
| MBPP dev task list | 40 | `513792c8394b93c590df0d90ab7d79d8a7beaef95e111eaf4e27cbb4c6559d0b` |
| Combined 80-task list | 80 | `e79b5382419fa0cbdd0df5e34dd08a4d421f8c71f1720c37fcc51608b62a0af0` |

The list hash is SHA-256 of the canonical JSON array `json.dumps(task_ids, separators=(",", ":"))`. The task IDs are the exact `humaneval.dev` and `mbpp.dev` lists from `splits.json`; the 80-task combined list is the sorted union. The `run_eval.py` reads the same `splits.json`, so the IDs are not retyped.

## 4. Model and tool hashes

| item | value |
|---|---|
| model path | `C:\Users\Anton\.lmstudio\apps\bionic\projects\d49037d8-47f4-5808-9028-c707de117f8f\workspace\LLM intagration\harness\models\Qwen2.5-Coder-1.5B-Instruct\quants\q3km_code.gguf` |
| model SHA-256 | `fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb` |
| model size | 824,179,104 bytes (786.0 MiB) |
| KV cache | `q8_0` |
| backend | CPU, 6 threads, context 2048 |
| server build | `llama.cpp b12069-cpu` |
| runner | `harness/scripts/run_eval.py` in the main workspace |

The model path is in the **main workspace**, not in this worktree. The run script therefore uses `--model` with the absolute path rather than `--config-id`; the worktree's `quant_path("q3km_code")` would resolve to a missing file. The SHA was verified with `Get-FileHash` on the actual file.

## 5. Run script and exact command

Script: `harness/architect/agents/04_routing/run_v6_kv8_80.ps1`.

**Exact command for the lead after the 40-task panel:**

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Anton\.lmstudio\apps\bionic\projects\d49037d8-47f4-5808-9028-c707de117f8f\workspace\LLM intagration\.kilo\worktrees\arrow-chronometer\harness\architect\agents\04_routing\run_v6_kv8_80.ps1" -Port 8140
```

What the script does:

1. Verifies the model SHA-256 and `splits.json` SHA-256; aborts on mismatch.
2. Acquires the eval lock via `python harness/team/scripts/eval_lock.py acquire --branch agent-04-routing-v6-kv8 --port 8140 --timeout 3600`.
3. Runs HumanEval dev 40:
   `python harness/scripts/run_eval.py --model <model> --label v6_kv8_he_dev --backend cpu --threads 6 --context 2048 --kv-cache q8_0 --dataset humaneval --split dev --max-tokens 512 --temperature 0.0 --request-timeout 600 --test-timeout 30 --port 8140 --output harness/results/v6/v6_kv8_he_dev.jsonl`
4. Runs MBPP dev 40 with the same protocol and `--dataset mbpp --split dev --output harness/results/v6/v6_kv8_mbpp_dev.jsonl`.
5. Releases the lock in a `finally` block.
6. Runs both Python processes at **BelowNormal** priority; logs to `harness/architect/agents/04_routing/v6_kv8_run.log`.

The script does not start anything until the lead runs it. It refuses to proceed if the lock is held or the hashes differ. It does not use `--force`, `steal`, or a GPU.

## 6. Outputs and verification

After the run, the main workspace will contain:

- `harness/results/v6/v6_kv8_he_dev.jsonl` and `_summary.json` / `_summary.md` (40 tasks).
- `harness/results/v6/v6_kv8_mbpp_dev.jsonl` and `_summary.json` / `_summary.md` (40 tasks).

The summaries record `model_sha256`, `kv_cache`, `dataset`, `split`, `task_count`, `passed`, and the server command. The lead should verify:

- `task_count` is 40 for each file and the task IDs match `v6_kv8_split_ids.json`.
- `model_sha256` is `fbc804...`.
- `kv_cache` is `q8_0`.
- The request-error rate is below 10%; otherwise the protocol allows one repeat, not a post-hoc deletion.

The 13×80 matrix is then the 12 current configurations plus `q3km_code_kvq8_0_preplus`, with the 80 task IDs in the combined list.

**Table separation (do not merge).** The V6 run does not retroactively change the two common-config tables:

- **14×60→12×80 (common-config):** source is the 12-common-config 14×60 pair (`q3km_code_preplus` + `mx_q4km_code_attnq_q5k_plus`), source union **39/60**; target oracle **56/80**; selected **48/80**; regret 8.0; MAE rate 0.0630; top-3 0.0.
- **12×80→14×60 (common-config):** source is 12×80 (56/80); target oracle is the **39/60 common-config oracle**, not the full 14-config 41/60; selected **34/60**; regret 5.0; MAE rate 0.0630; top-3 0.0.

The new KV8-inclusive table is separate:

- **14×60→13×80:** source is the full 14×60 pair **41/60** (KV8 included); target oracle is the best pair among the 13; the target is **not** the 39/60 common-config oracle.
- **13×80→14×60:** source is the 13×80 best pair; target oracle is the full 14×60 **41/60** (KV8 included), not the 39/60 common-config oracle.

Do not merge the 39/60 common-config target with the 41/60 full oracle. The 39/60 row stays a common-config row; the 41/60 row is the KV8-inclusive residual row.

## 7. Resource estimate

The KV8 heldout 60-task run in `harness/results/finalist_q3km_code_kv8_humaneval_heldout_summary.json` took 869.25 CPU-s and 148.36 wall-s (14.49 CPU-s/task, 2.47 wall-s/task). Scaling to 80 tasks:

- CPU: about 1,159 CPU-s = **19.3 CPU-min**; budget 25 CPU-min.
- Wall: about 198 s = **3.3 min**; budget 6 min including two server loads.
- Server loads: 2 (one per `run_eval.py` invocation); lock acquisitions: 1.
- Memory: about 1.1 GiB server RSS; disk: a few MB of JSONL.
- GPU: none. Priority: BelowNormal.

The 40-task panel runs first; this 80-generation run is below-normal and should not overlap a T0 run. The lead owns the port and the window.

## 8. What this does not do

- It does not add `q4km_code_preplus`; a full 14×80 matrix would need a second 80-generation run.
- It does not reuse the KV8 MBPP dev cells already in `paired.csv`; the run is a matched 80-task protocol.
- It does not start the run, acquire the lock, or touch the server. The lead launches after the 40-task panel.
- It does not change the V6 claim; it only removes the common-config confound for the KV8-inclusive cross-matrix test.

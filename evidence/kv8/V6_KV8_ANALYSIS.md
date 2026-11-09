# V6 KV8-inclusive 13×80 cross-matrix analysis

**Agent:** `04_routing`  
**Date:** 2026-11-09  
**Scope:** Analysis-only, CPU-only. No scored run, server, lock, GPU, new session, or commit. Writes only under `harness/architect/agents/04_routing/`.  
**Inputs:** `V6_KV8_CROSS_MATRIX_PLAN.md`; `paired.csv`; the completed KV8 outputs `harness/results/v6/v6_kv8_he_dev.jsonl` and `v6_kv8_mbpp_dev.jsonl`; `v6_kv8_split_ids.json`.

## 1. The 13×80 matrix

The KV8 run is `q3km_code` with `q8_0` KV: HumanEval dev **23/40 (57.5%)**, MBPP dev **22/40 (55.0%)**. Both files have 40 rows and the expected task IDs. Adding KV8 to the 12×80 matrix gives 13 configurations × 80 tasks:

| matrix | best fixed | union | best pair | best pair union |
|---|---:|---:|---|---:|
| 14×60 heldout | 36/60 | 43/60 | `q3km_code_kvq8_0_preplus` + `mx_q4km_code_attnq_q5k_plus` | 41/60 |
| 12×80 | 49/80 | 58/80 | `mx2_aq6_q3ks_plus` + `mx_q3km_code_gateup_q4k_plus` | 56/80 |
| **13×80 (KV8 added)** | **49/80** | **58/80** | `mx2_aq6_q3ks_plus` + `mx_q3km_code_gateup_q4k_plus` | **56/80** |

**KV8 adds zero union.** Its dev passes are already covered by the 12×80 pool; the 13×80 union stays 58/80 and the best pair stays 56/80. KV8 is not a complementarity source on these 80 tasks; it is a 23/40 and 22/40 config whose passes are a subset of the pool's coverage.

## 2. Within-sample exactness

The exact header is the pass-set bitset: **10 B per configuration for 80 tasks**. Within the observed 13×80 matrix, pair/union selection is exact by construction: **0.00 regret, 0.0000 MAE, 1.00 top-3, CP@1 1.000**. The storage claim is unchanged; KV8 simply adds one 10 B row.

## 3. Split-half on 13×80

Two thousand random 40/40 splits; select the pair with the highest training-half union, evaluate on the test half. Regret/MAE are in tasks; MAE rate is tasks / test size.

| metric | 13×80 (KV8) | Qwen 14×60 | Qwen 12×80 |
|---|---:|---:|---:|
| regret mean [2.5, 97.5] | 1.73 [0.00, 4.00] | 1.91 [0, 6] | 1.70 [0, 4] |
| MAE tasks (rate) | 3.38 (0.0846) | 3.00 (0.100) | 3.47 (0.087) |
| top-3 | 0.121 | 0.208 | 0.079 |
| CP@1 | 0.051 | n/r | n/r |
| full-best selected | 0.432 | n/r | n/r |

The out-of-sample boundary is unchanged: the exact header does not make selection out-of-sample exact. The 13×80 MAE is 3.38 tasks (0.0846), in the same range as the Qwen 14×60/12×80 split-half (3.00/3.47 tasks). The top-3 is 0.121, between the Qwen 0.079 and 0.208; CP@1 is 0.051. KV8 does not rescue the split-half rule.

## 4. Cross-matrix

The two common-config tables and the two KV8-inclusive tables are kept separate. The 39/60 target is the **12-common-config oracle**, not the full 14-config 41/60.

### 4.1 KV8-inclusive (13 common configurations)

| direction | selected pair | selected/target | target oracle | regret | MAE rate | top-3 | target-best |
|---|---|---|---:|---:|---:|---:|---:|
| **14×60→13×80** | `q3km_code_kvq8_0_preplus` + `mx_q4km_code_attnq_q5k_plus` | **49/80** | **56/80** | **7** | **0.0579** | **0** | **0** |
| **13×80→14×60** | `mx2_aq6_q3ks_plus` + `mx_q3km_code_gateup_q4k_plus` | **34/60** | **41/60** | **7** | **0.0579** | **0** | **0** |

### 4.2 Common-config (12 configurations; the existing V4 tables)

| direction | selected pair | selected/target | target oracle | regret | MAE rate | top-3 | target-best |
|---|---|---|---:|---:|---:|---:|---:|
| 14×60→12×80 | `q3km_code_preplus` + `mx_q4km_code_attnq_q5k_plus` | 48/80 | 56/80 | 8 | 0.0630 | 0 | 0 |
| 12×80→14×60 | `mx2_aq6_q3ks_plus` + `mx_q3km_code_gateup_q4k_plus` | 34/60 | **39/60** (common-config) | 5 | 0.0630 | 0 | 0 |

**What KV8 changes.** In the 14×60→13×80 direction, the full 14×60 best pair (KV8 + `mx_q4km_code_attnq_q5k_plus`) now evaluates on the target: 49/80 vs 56/80, regret 7, MAE 0.0579. The common-config 14×60→12×80 selected 48/80, regret 8, MAE 0.0630. KV8 buys **one task** and a slightly lower MAE, but the target-best pair is still not selected and top-3 is still 0.

In the 13×80→14×60 direction, the selected pair is the same `mx2_aq6 + gateup` pair at 34/60, but the target oracle is now the **full 41/60** (KV8 included), not the 39/60 common-config oracle. The selected union is unchanged at 34/60; the full oracle is 2 tasks higher, so regret rises from 5 to 7. MAE improves slightly (0.0630→0.0579), but top-3 and target-best remain 0.

## 5. Verdict

**The KV8-inclusive boundary does not change the V6 conclusion.** The exact header remains exact within the observed 13×80 matrix (10 B/config, 0.00 regret, 0.0000 MAE, 1.00 top-3, CP@1 1.000), but transfer still fails:

- **Split-half:** 1.73 tasks regret, 3.38 tasks MAE (0.0846), top-3 0.121, CP@1 0.051. The exact header does not make the selection rule out-of-sample exact.
- **Cross-matrix:** target-best pair selected **0/2** KV8-inclusive directions; top-3 **0/2**; regret **7 tasks** in both; MAE **0.0579**. The source-selected pair is never the target best.
- **KV8 adds zero union:** the 13×80 union is 58/80 and the best pair is 56/80, identical to the 12×80 matrix. KV8 is not a complementarity source on these tasks.
- **The only numerical improvement** is the 14×60→13×80 source pair: 49/80 vs 48/80, regret 8→7, MAE 0.0630→0.0579. The 13×80→14×60 selected union is unchanged at 34/60; the full oracle is 41/60 instead of 39/60, so regret rises 5→7. The full oracle is harder, not easier.

**Top number:** **13×80 exact header 10 B/config, 0.00 within-sample regret/MAE, 1.00 top-3; KV8 adds 0 union (13×80 union 58/80, best pair 56/80); KV8-inclusive cross-matrix target-best 0/2, top-3 0/2, regret 7 tasks, MAE 0.0579.** The V6 conclusion is unchanged: exact storage for the observed matrix, not out-of-sample or cross-matrix selection.

## 6. Caveats

- The 13×80 matrix is not the full 14×80 matrix; `q4km_code_preplus` is still absent (it lacks MBPP dev 40). A full 14×80 would need another 80 generations and could change the target oracle.
- KV8's dev pass rates (23/40, 22/40) are below the 12×80 best fixed 49/80; its passes are covered by the pool. This is a property of these 80 tasks, not a general statement about KV8.
- The 13×80 split-half and cross-matrix are 78-pair estimates on 80 tasks; the intervals are split-to-split, not population intervals.
- The 39/60 row remains the common-config oracle; do not merge it with the full 41/60 row. The KV8-inclusive row uses the full 41/60 target.
- The exact header is task-specific; the cross-matrix is a configuration-pair transfer, not a header transfer.

## 7. Reproduction

`v6_kv8_analysis.py` reads `paired.csv` and the two KV8 JSONLs, verifies the 80 task IDs, builds the 13×80 matrix, and writes `v6_kv8_analysis_output.json` / `v6_kv8_analysis_output.txt`. No scored run, server, lock, GPU, new session, or commit was used.

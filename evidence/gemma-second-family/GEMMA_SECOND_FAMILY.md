# Gemma second-family evidence: exact headers and the transfer boundary

**Agent:** `04_routing`  
**Date:** 2026-11-09  
**Scope:** Analysis-only, CPU-only. No scored run, server, lock, GPU, new session, or commit. Writes only under `harness/architect/agents/04_routing/`.  
**Data:** `team-predictor-core-8b4a5ef629618ecf/harness/predictor/results/gemma_complementarity/gemma_complementarity.json`; the five Gemma configs' JSONLs from `team-mixed-precision-2-e4a2c8e571a64e74/harness/results/mixed/gemma*`. The JSON's own interpretation is "OFFLINE ORACLE UPPER BOUNDS; NOT deployable selection/performance"; this note inherits that scope.

## 1. Data and method

Five configurations: `q3_mix`, `google_qat_q4_0`, `gp1_qat_requant`, `udq4_k_xl`, `udq2_k_xl`. Three splits: HumanEval dev 40, HumanEval heldout 60, MBPP heldout 60. The per-task pass vectors were read from the JSONLs and checked against the complementarity JSON's `model_pass` counts; all five configs and all three splits match exactly:

| split | n | q3_mix | google_qat_q4_0 | gp1_qat_requant | udq4_k_xl | udq2_k_xl |
|---|---:|---:|---:|---:|---:|---:|
| HumanEval dev | 40 | 25 | 29 | 29 | 29 | 15 |
| HumanEval heldout | 60 | 35 | 34 | 34 | 36 | 17 |
| MBPP heldout | 60 | 30 | 35 | 32 | 35 | 21 |

The **exact header** is the pass-set bitset: 5 B per configuration for 40 tasks, 8 B for 60 tasks. Within-sample pair union is the popcount of the OR, so pair/union selection is exact by construction. The **split-half** selects the pair with the highest union on a random half and evaluates it on the other half. The **cross-matrix** selects the pair with the highest union on a source split and evaluates it on a target split. The Qwen reference is the V4 input's split-half and cross-matrix table.

## 2. Within-sample exactness

| split | header | best pair | union | regret | MAE | top-3 | CP@1 |
|---|---:|---|---:|---:|---:|---:|---:|
| HumanEval dev | **5 B** | q3_mix + google_qat_q4_0 | 33/40 | 0 | 0 | 1.00 | 1.000 |
| HumanEval heldout | **8 B** | q3_mix + udq4_k_xl | 43/60 | 0 | 0 | 1.00 | 1.000 |
| MBPP heldout | **8 B** | gp1_qat_requant + udq4_k_xl | 38/60 | 0 | 0 | 1.00 | 1.000 |

The storage result replicates exactly: a 5 B/40 and 8 B/60 bitset stores the observed pass set losslessly, and the pair selection is exact within the observed matrix. This is a construction, not a prediction.

## 3. Split-half boundary

Two thousand random 50/50 splits per matrix. Regret and MAE are in tasks; MAE rate is tasks divided by the test size. The Qwen reference is the V4 input's split-half table.

| matrix | n | header | regret mean [2.5, 97.5] | MAE tasks (rate) | top-3 | CP@1 | full-best selected |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemma HumanEval dev | 40 | 5 B | 1.36 [0.00, 4.00] | 2.12 (0.1062) | 0.513 | 0.176 | 0.572 |
| Gemma HumanEval heldout | 60 | 8 B | 0.57 [0.00, 1.00] | 3.02 (0.1007) | 0.969 | 0.000 | 0.507 |
| Gemma MBPP heldout | 60 | 8 B | 1.59 [0.00, 4.00] | 2.98 (0.0995) | 0.050 | 0.000 | 0.276 |
| Qwen 14×60 | 60 | 8 B | 1.91 [0, 6] | 3.00 (0.100) | 0.208 | n/r | n/r |
| Qwen 12×80 | 80 | 10 B | 1.70 [0, 4] | 3.47 (0.087) | 0.079 | n/r | n/r |

The **out-of-sample boundary replicates**: the exact header does not make the pair-selection rule out-of-sample exact. Gemma's split-half MAE is 2.1–3.0 tasks (0.100–0.106), essentially the same as Qwen's 3.0–3.5 tasks (0.087–0.100). The regret is family-dependent: Gemma heldout 0.57 tasks is lower than Qwen's 1.7–1.9; MBPP 1.59 is in the Qwen range. The top-3 is the most variable: Gemma heldout 0.969 is high, MBPP 0.050 is low, dev 0.513 is intermediate. CP@1 is 0.000 on both 60-task Gemma splits, meaning the selected pair is never the exact best pair even when the best pair is in the top-3. The Gemma split-half full-best-selected fraction is 0.276–0.572. The Qwen V4 input's 0.405/0.411 is a configuration-resample metric, not a split-half metric; the two are not directly comparable.

## 4. Cross-matrix boundary

All six ordered directions. The selected pair is the source-split best; the target oracle is the target-split best; `target-best` is 1 only if the selected pair is the target best. MAE rate is the mean absolute source-target union-rate difference over the 10 pairs.

| direction | selected pair | selected/target | target oracle | regret | MAE rate | top-3 | target-best |
|---|---|---|---:|---:|---:|---:|---:|
| dev → heldout | q3_mix + google_qat_q4_0 | 42/60 | 43/60 | 1 | 0.1325 | 0 | 0 |
| dev → MBPP | q3_mix + google_qat_q4_0 | 36/60 | 38/60 | 2 | 0.1808 | 0 | 0 |
| heldout → dev | q3_mix + udq4_k_xl | 31/40 | 33/40 | 2 | 0.1325 | 1 | 0 |
| heldout → MBPP | q3_mix + udq4_k_xl | 37/60 | 38/60 | 1 | 0.0550 | 0 | 0 |
| MBPP → dev | gp1_qat_requant + udq4_k_xl | 32/40 | 33/40 | 1 | 0.1808 | 0 | 0 |
| MBPP → heldout | gp1_qat_requant + udq4_k_xl | 37/60 | 43/60 | 6 | 0.0550 | 1 | 0 |

For comparison, the Qwen cross-matrix table gives 14×60→12×80: 48/80 vs 56/80, regret 8.0, MAE 0.0630, top-3 0.0; 12×80→14×60: 34/60 vs 39/60, regret 5.0, MAE 0.0630, top-3 0.0. The target oracle is never the selected pair in either Qwen direction.

The **transfer failure replicates in the decisive sense**: the source-selected pair is **not the target best pair in any of the six Gemma directions** (`target-best 0/6`). The target-best pair is in the source top-3 in two directions (heldout→dev, MBPP→heldout), but top-1 selection still fails. The regret magnitude is family-dependent: 1–6 tasks, mostly lower than Qwen's 5–8. The MAE rate is 0.055–0.181, wider than Qwen's 0.063. The exact Qwen numbers do not transfer; the qualitative boundary does.

## 5. Verdict

**The Qwen storage boundary replicates exactly. The Qwen transfer boundary replicates qualitatively, not numerically.**

- **Storage:** 5 B per configuration for 40 tasks, 8 B for 60 tasks; within-sample 0 regret, 0 MAE, 1.00 top-3, CP@1 1.000. This is family-independent because it is a bitset of the observed pass set.
- **Split-half:** the exact header does not make selection out-of-sample exact. Gemma MAE 2.1–3.0 tasks (0.100–0.106), matching Qwen's 3.0–3.5 (0.087–0.100); CP@1 is 0.000 on both 60-task splits; the full-matrix best pair is selected in 27.6–57.2% of splits.
- **Cross-matrix:** the source-selected pair is not the target best pair in 0/6 directions; regret 1–6 tasks; MAE 0.055–0.181. Qwen's 5–8 task regret and 0.063 MAE are not reproduced, but the target-best failure is.

**Top number:** **5 B/40 and 8 B/60 exact headers, 0.00 within-sample regret/MAE, 1.00 top-3; transfer fails with the target-best pair selected 0/6 cross-matrix directions (regret 1–6 tasks).** The best transfer case is heldout→MBPP (37/60 vs 38/60, regret 1); the worst is MBPP→heldout (37/60 vs 43/60, regret 6).

## 6. Caveats

- Five configs and ten pairs make the split-half and cross-matrix estimates noisy. The 2000-split intervals are split-to-split, not population intervals.
- The Gemma splits are different task sets; the cross-matrix is a configuration-pair transfer, not a header transfer. The exact header is task-specific and does not transfer its bits.
- The JSON's own interpretation is offline oracle upper bounds, not deployable selection. This note does not claim deployment.
- The Qwen split-half CP@1 is not reported in the V4 input; the comparison uses the Qwen regret/MAE/top-3 and full-best-selected numbers only.
- The Gemma top-3 is high on heldout (0.969) but CP@1 is 0.000; the target best is in the top-3 but never first. This is a real distinction, not a rounding artifact.

## 7. Reproduction

`gemma_second_family.py` reads the five JSONLs per split, verifies the pass counts against `gemma_complementarity.json`, and writes `gemma_second_family_output.json` and `gemma_second_family_output.txt`. No scored run, server, lock, GPU, new session, or commit was used.

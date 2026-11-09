# External selector baseline: exact header vs sketches and a learned selector

**Agent:** `04_routing`  
**Date:** 2026-11-09  
**Scope:** Analysis-only, CPU-only. No scored run, server, lock, GPU, new session, or commit. Writes only under `harness/architect/agents/04_routing/`.  
**Inputs:** `exact_header_output.json` (exact header, MinHash-512, Bloom-512, random projection within-sample); `external_selector_output.json` (learned selector and all out-of-sample comparisons); the 14×60 and 12×80 matrices from `paired.csv`.

## 1. Selectors and matched bytes

| selector | storage per config | method |
|---|---:|---|
| **exact header** | **8 B (60 tasks), 10 B (80 tasks)** | pass-set bitset; exact union by popcount |
| MinHash-512 | 2,048 B | 512 32-bit minima; Jaccard/union estimate |
| Bloom-512 | 64 B | 512-bit Bloom, 3 hashes; fill-rate union estimate |
| random projection | 8 B (60), 10 B (80) | \(d=\lceil n/8\rceil\) int8 dimensions; \(\hat I=y_a\cdot y_b\) |
| learned L1 logistic | **7.5 B** | 14 public task features, 15 four-bit parameters; predicts each config's pass probability, selects the pair with the highest predicted union |

The learned selector uses only public, pre-run task features: dataset (HumanEval/MBPP), reference prompt-token quartile, reference completion-token quartile, task-id bucket mod 4, and reference truncation. It is trained per configuration with L1 logistic regression; weights and intercept are quantized to four bits on a fixed \([-4,4]\) grid (15 values × 4 bits = 7.5 B). It fits the exact-header budget (8/10 B) and is a standard public/learned selector, not a strawman: it is the best of the simple feature-based selectors we tried.

## 2. Within-sample

| matrix | selector | regret | union MAE | top-3 | CP@1 |
|---|---|---:|---:|---:|---:|
| 14×60 | **exact header (8 B)** | **0.00** | **0.0000** | **1.00** | **1.000** |
| 14×60 | MinHash-512 (2,048 B) | 0.00 | 0.0079 | 1.00 | 1.000 |
| 14×60 | Bloom-512 (64 B) | 0.24 | 0.0222 | 0.95 | 0.905 |
| 14×60 | random projection (8 B) | 4.00 | 0.0555 | 0.02 | 0.015 |
| 14×60 | learned L1 (7.5 B) | 1.00 | 0.2618 | 0.00 | 0.000 |
| 12×80 | **exact header (10 B)** | **0.00** | **0.0000** | **1.00** | **1.000** |
| 12×80 | MinHash-512 (2,048 B) | 0.04 | 0.0056 | 0.99 | 0.965 |
| 12×80 | Bloom-512 (64 B) | 0.13 | 0.0306 | 0.94 | 0.935 |
| 12×80 | random projection (10 B) | 2.00 | 0.0452 | 0.01 | 0.000 |
| 12×80 | learned L1 (7.5 B) | 10.00 | 0.2873 | 0.00 | 0.000 |

**Within-sample, nothing beats the exact header.** It is the pass set, so pair selection is exact by construction. The learned selector is the worst of the approximate selectors; its 14 public features and 4-bit weights are not enough to reconstruct the pass pattern. MinHash-512 is the best approximate selector, but it is 256× larger and still not exact.

## 3. Split-half (out-of-sample)

Two hundred random 50/50 splits; select on one half, evaluate on the other. Regret and MAE are in tasks; MAE rate is tasks / test size. The exact header and sketches select by their training-half union estimate; the learned selector predicts per-task pass probabilities and selects the pair with the highest predicted union.

| matrix | selector | regret | MAE tasks (rate) | top-3 | CP@1 |
|---|---|---:|---:|---:|---:|
| 14×60 | exact header | **1.90** | 3.06 (0.1019) | **0.204** | **0.000** |
| 14×60 | MinHash-512 | 2.10 | 3.08 (0.1028) | 0.185 | 0.005 |
| 14×60 | Bloom-512 | 2.08 | 3.10 (0.1032) | 0.160 | 0.000 |
| 14×60 | random projection | 3.08 | 3.73 (0.1243) | 0.205 | 0.000 |
| 14×60 | learned L1 | 3.38 | 8.48 (0.2825) | 0.050 | 0.010 |
| 12×80 | exact header | 1.70 | 3.45 (0.0863) | 0.080 | 0.047 |
| 12×80 | **MinHash-512** | **1.45** | **3.26 (0.0814)** | **0.150** | **0.120** |
| 12×80 | Bloom-512 | 1.64 | 3.36 (0.0840) | 0.135 | 0.085 |
| 12×80 | random projection | 1.49 | 3.97 (0.0992) | 0.220 | 0.160 |
| 12×80 | learned L1 | 3.04 | 11.44 (0.2859) | 0.075 | 0.035 |

**A selector beats the exact header on the 12×80 split-half.** MinHash-512 has lower regret (1.45 vs 1.70), lower MAE (3.26 vs 3.45 tasks; 0.0814 vs 0.0863), higher top-3 (0.150 vs 0.080), and higher CP@1 (0.120 vs 0.047). The exact header's training-half union selection overfits the 30-task half; the sketch's noise regularizes it. The random projection also beats the exact header on regret/top-3/CP@1 for 12×80 but has worse MAE (3.97 vs 3.45). On the 14×60 split-half, the exact header is best on regret and top-3; CP@1 is 0.000 for the exact header and Bloom, 0.005 for MinHash. MinHash/Bloom have slightly higher regret and similar MAE. The learned selector is worse than the exact header and the sketches on both matrices.

## 4. Cross-matrix (12 common configs)

| direction | selector | regret | MAE rate (tasks) | top-3 | CP@1 |
|---|---|---:|---:|---:|---:|
| 14×60→12×80 | exact header | 8 | 0.0630 (5.04) | 0 | 0 |
| 14×60→12×80 | MinHash-512 | 8 | 0.0617 (4.93) | 0 | 0 |
| 14×60→12×80 | Bloom-512 | 8 | 0.0575 (4.60) | 0 | 0 |
| 14×60→12×80 | random projection | **6** | 0.1134 (9.07) | 0 | 0 |
| 14×60→12×80 | learned L1 | 7 | 0.2521 (20.17) | 0 | 0 |
| 12×80→14×60 | exact header | 5 | 0.0630 (3.78) | 0 | 0 |
| 12×80→14×60 | MinHash-512 | 5 | 0.0566 (3.40) | 0 | 0 |
| 12×80→14×60 | Bloom-512 | 5 | 0.0954 (5.73) | 0 | 0 |
| 12×80→14×60 | random projection | **4** | **0.0323 (1.94)** | 0 | 0 |
| 12×80→14×60 | learned L1 | 7 | 0.3350 (20.10) | 0 | 0 |

**No selector changes the cross-matrix boundary.** The target-best pair is never in the predicted top-3 and is never selected (top-3 0, CP@1 0) for every selector and both directions. The random projection reduces regret on 12×80→14×60 (4 vs 5) and MAE (0.0323 vs 0.0630), but it does not find the target-best pair; it also has worse MAE on 14×60→12×80 (0.1134 vs 0.0630). MinHash-512 and Bloom-512 slightly reduce MAE but not regret/top-3/CP@1. The learned selector is worse on both directions (regret 7/7, MAE 0.2521/0.3350).

## 5. Verdict

**Within-sample, the exact header is unbeatable: 0.00 regret, 0.0000 MAE, 1.00 top-3, CP@1 1.000 at 8/10 B. No selector beats it or ties it except MinHash-512 at 2,048 B, which ties the 14×60 exactness but is 256× larger.**

**Out-of-sample, the boundary is not absolute.** MinHash-512 beats the exact header on the 12×80 split-half on all four metrics (regret 1.45 vs 1.70; MAE 3.26 vs 3.45 tasks; top-3 0.150 vs 0.080; CP@1 0.120 vs 0.047). The random projection at matched 8/10 B beats the exact header on 12×80→14×60 regret/MAE (4 vs 5; 0.0323 vs 0.0630) but not top-3/CP@1. The exact header remains best on the 14×60 split-half on regret and top-3 (CP@1 is 0.000 for the exact header and Bloom, 0.005 for MinHash), and the learned selector is worse than the exact header everywhere.

**The V6 cross-matrix conclusion is unchanged:** no selector selects the target-best pair or puts it in the top-3 in either direction. The exact header's exactness is a within-sample storage property; the transfer boundary survives the external baselines. The only boundary change is the 12×80 split-half, where MinHash-512's 2 KB sketch regularizes the training-half overfit and beats the 8/10 B exact header; this is a quantitative out-of-sample nuance, not a cross-matrix rescue.

**Top number:** **MinHash-512 beats the exact header on the 12×80 split-half: regret 1.45 vs 1.70, MAE 3.26 vs 3.45 tasks (0.0814 vs 0.0863), top-3 0.150 vs 0.080, CP@1 0.120 vs 0.047; but no selector beats the exact header within-sample (0/0/1/1) or changes the cross-matrix target-best failure (all selectors top-3/CP@1 0/0).**

## 6. Caveats

- The learned selector is a 14-feature, 4-bit L1 logistic at 7.5 B/config. It is a fair matched-budget baseline, not a tuned model; a larger learned selector would exceed the exact-header budget.
- The split-half is 30/30 (14×60) and 40/40 (12×80); the MinHash-512 advantage on 12×80 is a 200-split mean and may not transfer. The exact header remains the best within-sample and the best at 8/10 B on 14×60.
- The cross-matrix uses the 12 common configurations; the KV8-inclusive 13×80 analysis is separate. The 39/60 target is the common-config oracle, not the full 41/60.
- The exact header is task-specific; the sketches and learned selector are also trained on the observed matrices. None is a deployment guarantee.
- No scored run, server, lock, GPU, new session, or commit was used.

## 7. Reproduction

`external_selector.py` reads the 14×60 and 12×80 matrices, builds the 14 public features, fits the L1 logistic per configuration, and writes `external_selector_output.json` / `external_selector_output.txt`. The exact-header and sketch within-sample numbers are from `exact_header_output.json`; the split-half and cross-matrix sketch numbers are from the same script's out-of-sample extension.

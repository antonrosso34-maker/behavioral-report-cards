# Exact-header evidence: 8 B and 10 B pass-set headers vs MinHash, Bloom, and random projection

**Agent:** `04_routing`  
**Date:** 2026-11-09  
**Scope:** Analysis-only, CPU-only. No scored run, server, lock, GPU, new session, or commit. Writes only under `harness/architect/agents/04_routing/`.  
**Question:** For the existing 14×60 and 12×80 pass matrices, how do exact pass-set headers compare with MinHash-512, Bloom-512, and a random-projection selector at the same byte budget?

## 1. Exact header

A pass set is a subset of a fixed task suite. For \(n\) tasks, the exact header is the bitset \(b_c\in\{0,1\}^n\), stored in \(\lceil n/8\rceil\) bytes:

- **60 tasks:** 8 bytes per configuration (60 bits + 4 spare).
- **80 tasks:** 10 bytes per configuration (80 bits).

The pair union is the popcount of the bitwise OR: \(u_{ab}=\operatorname{popcount}(b_a\lor b_b)\). The pair selection is exact: choose the pair with the largest popcount union. The header is deterministic, has no hash seed, and needs no pass count (the popcount gives it). It is the gold standard for a fixed task suite.

## 2. Methods compared

| method | size (60 tasks) | size (80 tasks) | notes |
|---|---:|---:|---|
| exact bitset | **8 B** | **10 B** | exact union; no seed |
| MinHash-512 | 2,048 B | 2,048 B | 512 minima × 32-bit values |
| Bloom-512 | 64 B | 64 B | 512-bit Bloom, 3 hashes |
| MinHash-64 | 256 B | 256 B | 64 minima × 32-bit values |
| Bloom-64 | 8 B | 8 B | 64-bit Bloom, 3 hashes |
| random projection | 8 B | 10 B | \(d=\lceil n/8\rceil\) int8 dimensions, shared random ±1 matrix; \(\hat I=y_a\cdot y_b\), \(\hat u=|A|+|B|-\hat I\), clipped |

The random projection is matched to the exact-header budget: 8 int8 dimensions for 60 tasks (8 B), 10 for 80 tasks (10 B). It is an unbiased linear sketch of the intersection but has high variance at this dimension.

**Protocol.** For MinHash and Bloom we run 200 independent hash seeds; for the random projection we run 200 independent random matrices. For each seed we estimate all pairwise unions, select the pair with the highest estimated union, and record:

- **regret** = true best-pair union minus the true union of the selected pair, in tasks;
- **union MAE** = mean absolute error over all pairs, in tasks and as a rate (tasks / n);
- **top-3** = 1 if the true best pair is in the three pairs with the highest estimated union;
- **regret+MAE bars** = regret <1 task and MAE <0.03 rate; top-3 is reported separately. The all-four intersection (regret+MAE+top-3+CP@1) is not separately estimated.

The exact header is deterministic, so its metrics are single values. Full output: `exact_header_output.json`; script: `exact_header.py`.

## 3. Results

### 3.1 Heldout 14×60 (true best pair 41/60)

| method | size | regret mean [2.5, 97.5] | zero-regret seeds | MAE (tasks) | MAE rate | top-3 | regret+MAE bars |
|---|---:|---:|---:|---:|---:|---:|---:|
| **exact bitset** | **8 B** | **0.00** | **1.00** | **0.0000** | **0.0000** | **1.00** | **1.00** |
| MinHash-512 | 2,048 B | 0.00 [0.00, 0.00] | 1.00 | 0.4730 | 0.0079 | 1.00 | 1.00 |
| Bloom-512 | 64 B | 0.24 [0.00, 4.00] | 0.91 | 1.3290 | 0.0222 | 0.95 | 0.71 |
| MinHash-64 | 256 B | 0.14 [0.00, 2.00] | 0.92 | 0.9614 | 0.0160 | 0.99 | 0.87 |
| Bloom-64 | 8 B | 2.17 [0.00, 6.00] | 0.14 | 5.9578 | 0.0993 | 0.47 | 0.03 |
| random projection 8d | 8 B | 4.00 [2.98, 6.00] | 0.01 | 3.3280 | 0.0555 | 0.02 | 0.00 |

**CP@1 (selected pair is the true best), heldout:** exact 1.000; MinHash-512 1.000; Bloom-512 0.905; MinHash-64 0.920; Bloom-64 0.145; random projection 0.015.

### 3.2 Fresh 12×80 (true best pair 56/80)

| method | size | regret mean [2.5, 97.5] | zero-regret seeds | MAE (tasks) | MAE rate | top-3 | regret+MAE bars |
|---|---:|---:|---:|---:|---:|---:|---:|
| **exact bitset** | **10 B** | **0.00** | **1.00** | **0.0000** | **0.0000** | **1.00** | **1.00** |
| MinHash-512 | 2,048 B | 0.04 [0.00, 1.00] | 0.96 | 0.4482 | 0.0056 | 0.99 | 0.96 |
| Bloom-512 | 64 B | 0.13 [0.00, 2.00] | 0.94 | 2.4477 | 0.0306 | 0.94 | 0.47 |
| MinHash-64 | 256 B | 0.71 [0.00, 2.00] | 0.58 | 1.0645 | 0.0133 | 0.81 | 0.57 |
| Bloom-64 | 8 B | 1.85 [0.00, 4.00] | 0.12 | 10.1535 | 0.1269 | 0.13 | 0.02 |
| random projection 10d | 10 B | 2.00 [2.00, 2.00] | 0.00 | 3.6178 | 0.0452 | 0.01 | 0.00 |

**CP@1 (selected pair is the true best), fresh:** exact 1.000; MinHash-512 0.965; Bloom-512 0.935; MinHash-64 0.585; Bloom-64 0.125; random projection 0.000.

## 4. Verdict

**The exact header wins, and it is not close.** On the 14×60 matrix, 8 B per configuration gives **0.00-task regret, 0.0000 union MAE, and 1.00 top-3**; on the 12×80 matrix, 10 B gives the same exactness. It is:

- **256× smaller** than MinHash-512 on the 60-task matrix (8 B vs 2,048 B), and **204.8× smaller** on the 80-task matrix (10 B vs 2,048 B);
- **8× smaller** than Bloom-512 on 60 tasks (8 B vs 64 B), and **6.4× smaller** on 80 tasks (10 B vs 64 B);
- exact, deterministic, and seed-free, while MinHash-512 and Bloom-512 are approximate and seed-dependent.

**Top number to quote:** **8 B/config exact header, 0-task regret, 0.0000 union MAE, 1.00 top-3 on the 14×60 matrix; 256× smaller than MinHash-512.** The 80-task header is 10 B/config with the same exactness, 204.8× smaller than MinHash-512. The separate MinHash-512 bars are regret+MAE 100%/96.5%, top-3 1.00/0.99, and CP@1 1.000/0.965; the all-four intersection is not separately estimated.

The matched-budget random projection fails: 8 int8 dimensions give 4.00-task mean regret and 0.0555 MAE on 60 tasks; 10 dimensions give 2.00-task regret and 0.0452 MAE on 80 tasks. A random linear sketch needs far more than 8–10 dimensions to resolve a 60–80-element pass set. Bloom-64 (8 B) is also poor (2.17-task regret, 0.0993 MAE on 60 tasks), so the exact bitset is the only 8 B representation that meets the regret+MAE bars. MinHash-512 meets the regret+MAE bars but pays 256× the bytes for no exactness gain; its separate top-3 is 1.00/0.99 and its CP@1 is 1.000/0.965; Bloom-512 is compact but its 0.0306 fresh MAE is at the bar and its 0.71/0.47 regret+MAE fractions are not stable.

## 5. What this changes

The earlier pass-set-sketch note recommended MinHash-256/512 because it assumed a large or unknown task suite. For the **current fixed suites of 60 and 80 tasks**, the exact bitset is the correct header: it is 8/10 B, exact, and smaller than every approximate sketch except Bloom-64 and the random projection, both of which fail the bars. The MinHash becomes relevant only when the task suite is much larger than the sketch budget: at 2,048 bits, the exact header reaches MinHash-512's size at 16,384 tasks. For a 60–80-task deployment, storing the exact pass set is both cheaper and better.

This also simplifies the paper's public-evidence story: an 8 B or 10 B header per configuration is trivially publishable, hashable, and auditable. There is no sketch seed to disclose and no approximation to defend. The header is a behavioral fact, not a model.

## 6. Caveats and falsification

- **Fixed task IDs.** The exact header is tied to a fixed task suite and ordering. It does not transfer to a new suite; a new suite needs a new header. The MinHash is the fallback when the suite is open-ended or much larger than 16k tasks.
- **Pass/fail only.** The header stores the outcome, not confidence or a per-task score. It is a set summary, not a router. The task-level routing negative result stands.
- **Small suites.** The result is for 60 and 80 tasks. At 200–300 tasks the exact header is 25–38 B/config, still small; at 16k tasks it is 2 KB, where MinHash becomes competitive. The crossover is a design choice, not a universal rule.
- **Falsification.** The exact-header claim is falsified if the pass-set bitset does not reproduce the pair unions exactly (it does by construction), or if a deployment requires a suite larger than the header budget and the approximate sketch is the only option. The approximate-selector comparison is falsified if MinHash-512 or Bloom-512 beats the exact header on regret/MAE at the same size; neither does at 8–10 B.

## 7. Recommendation

Store the exact pass-set bitset in the model metadata or sidecar: 8 B per configuration for the 60-task suite, 10 B for the 80-task suite. Use it for pair selection by popcount union. Keep MinHash-512 only as a fallback for task suites larger than 16,384 tasks or for open-ended evaluation. Do not use Bloom-64 or an 8–10 B random projection for this problem; they are dominated by the exact bitset at the same budget.

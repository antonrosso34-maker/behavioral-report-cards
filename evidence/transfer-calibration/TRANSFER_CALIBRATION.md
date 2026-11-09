# Transfer calibration: robust selection and prior shrinkage on 14×60 / 12×80

**Rule family:** `TRANSFER-CAL-01`.
**Status:** analysis-only. No scored run, server, lock, GPU, new session, or
commit.
**Data:** the 12 common configurations on the 14×60 HumanEval heldout and the
12×80 fresh dev matrices, reconstructed from
`harness/architect/data/paired.csv` (SHA-256
`51a6fd00c719301b49f256da7771ce12bd7969c1a474473123d3593634bfd180`).
**Reproduce:** `transfer_calibration.py` → `transfer_calibration_results.json`.

## 1. Rules

- **Baseline (uncalibrated exact header):** select the pair with the maximum
  point union rate on the training/source matrix.
- **Robust:** for each pair, compute the 10th percentile of the union rate
  across task-bootstrap resamples of the training/source matrix; select the
  pair with the highest 10th percentile. This is a lower-bound selector.
- **Prior shrinkage:** for each pair, score
  `(1−λ)·own_rate + λ·other_rate`, where `own_rate` is the training/target
  matrix's pair union rate and `other_rate` is the other matrix's full pair
  union rate; select the pair with the highest score. λ = 0.25, 0.50, 0.75.
- **Robust + prior:** the 10th percentile of the shrunk bootstrap scores.

**No-leakage design.** The strict cross-matrix rule selects on the source and
evaluates on the target; a source→target prior would use the target labels, so
it is not used. The prior shrinkage is tested in two legitimate ways: (i) the
split-half, where the other matrix's prior is applied to the training half and
the held-out half is untouched; (ii) target-selection with the source prior,
where the target's own pass sets plus the source prior select a pair and the
target-only exact header is the baseline. The target-only exact header is exact
on the target; the prior can only match it, not improve it, unless the target is
partially observed.

## 2. Split-half results (common 12-config matrices)

B=500 random 50/50 splits; task-bootstrap B=300 for the robust scores; test-half
size 30 tasks (14×60) and 40 tasks (12×80). Regret is reported as a rate and as
tasks on the test half. MAE is the union-rate error; “selected” is the error of
the selected pair's estimate, “overall” is the mean over all 66 pairs.

### 2.1 14×60

| Rule | Regret rate [95% CI] | Regret tasks | Top-3 [95% CI] | MAE selected | MAE overall |
|---|---:|---:|---:|---:|---:|
| Baseline | 0.0791 [0, 0.200] | 2.37 | 0.106 [0, 1] | 0.1181 | 0.1056 |
| Robust | 0.0820 [0, 0.200] | 2.46 | 0.108 [0, 1] | 0.1177 | 0.1056 |
| Prior λ=0.25 | 0.0937 [0, 0.200] | 2.81 | 0.046 [0, 1] | 0.1123 | 0.0937 |
| Prior λ=0.50 | 0.1022 [0.033, 0.200] | 3.07 | 0.002 [0, 0] | 0.1077 | 0.0841 |
| Prior λ=0.75 | 0.1054 [0.033, 0.200] | 3.16 | 0.006 [0, 0] | 0.1146 | 0.0786 |
| Robust+prior λ=0.25 | 0.0941 [0, 0.200] | 2.82 | 0.060 [0, 1] | 0.1114 | 0.0937 |

### 2.2 12×80

| Rule | Regret rate [95% CI] | Regret tasks | Top-3 [95% CI] | MAE selected | MAE overall |
|---|---:|---:|---:|---:|---:|
| Baseline | 0.0571 [0, 0.163] | 2.28 | 0.098 [0, 1] | 0.1012 | 0.0891 |
| Robust | 0.0573 [0, 0.175] | 2.29 | 0.100 [0, 1] | 0.1006 | 0.0891 |
| Prior λ=0.25 | 0.0500 [0, 0.150] | 2.00 | 0.044 [0, 1] | 0.0815 | 0.0792 |
| Prior λ=0.50 | 0.0641 [0, 0.175] | 2.56 | 0.042 [0, 1] | 0.0700 | 0.0715 |
| Prior λ=0.75 | 0.0938 [0, 0.175] | 3.75 | 0.060 [0, 1] | 0.0666 | 0.0688 |
| Robust+prior λ=0.25 | 0.0518 [0, 0.150] | 2.07 | 0.044 [0, 1] | 0.0825 | 0.0792 |

The robust rule is essentially the baseline: it selects the same or a
near-identical pair. The prior shrinkage improves the **union estimate** (MAE
overall 0.0937/0.0792 at λ=0.25 vs 0.1056/0.0891 baseline) but **worsens the
selection** top-3 (0.046/0.044 vs 0.106/0.098); at λ≥0.5 the top-3 collapses.
The fresh λ=0.25 regret is slightly lower (2.00 vs 2.28 tasks), but the top-3 is
worse; this is not a transfer win.

## 3. Cross-matrix results

The strict cross-matrix rule selects on the source and evaluates on the target.
The prior-target rows select on the target with the source prior and evaluate on
the target; the target-only exact header is the baseline.

### 3.1 14×60 → 12×80

| Rule | Selected pair | Source rate | Target rate | Target best | Regret (rate / tasks) | Top-3 | MAE overall |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline | pair 36 | 0.650 | 0.600 | 0.700 | 0.100 / 8.0 | 0.0 | 0.0630 |
| Robust | pair 36 | 0.650 | 0.600 | 0.700 | 0.100 / 8.0 | 0.0 | 0.0630 |
| Prior-target λ=0.25 | pair 52 | — | 0.700 | 0.700 | 0.000 / 0.0 | 1.0 | 0.0158 |
| Prior-target λ=0.50 | pair 34 | — | 0.675 | 0.700 | 0.025 / 2.0 | 0.0 | 0.0315 |
| Prior-target λ=0.75 | pair 36 | — | 0.600 | 0.700 | 0.100 / 8.0 | 0.0 | 0.0473 |
| Target-only | pair 52 | — | 0.700 | 0.700 | 0.000 / 0.0 | 1.0 | 0.0000 |

### 3.2 12×80 → 14×60

| Rule | Selected pair | Source rate | Target rate | Target best | Regret (rate / tasks) | Top-3 | MAE overall |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline | pair 52 | 0.700 | 0.567 | 0.650 | 0.083 / 5.0 | 0.0 | 0.0630 |
| Robust | pair 52 | 0.700 | 0.567 | 0.650 | 0.083 / 5.0 | 0.0 | 0.0630 |
| Prior-target λ=0.25 | pair 36 | — | 0.650 | 0.650 | 0.000 / 0.0 | 1.0 | 0.0158 |
| Prior-target λ=0.50 | pair 34 | — | 0.617 | 0.650 | 0.033 / 2.0 | 0.0 | 0.0315 |
| Prior-target λ=0.75 | pair 52 | — | 0.567 | 0.650 | 0.083 / 5.0 | 0.0 | 0.0473 |
| Target-only | pair 36 | — | 0.650 | 0.650 | 0.000 / 0.0 | 1.0 | 0.0000 |

The robust rule is **identical to the baseline** in both directions: the
10th-percentile ranking selects the same pair. The prior-target λ=0.25 matches
the **target-only exact header** (zero regret, top-3 1.0), but the target-only
header is already exact; the prior is redundant and has a worse union MAE
(0.0158 vs 0.0). At λ≥0.5 the prior degrades the target selection. The prior
does not improve the strict source→target rule, because that rule cannot use the
target labels without leakage.

## 4. Verdict

**Neither rule improves transfer; the negative boundary is sharpened.**

- **Robust selection does not help.** The 10th-percentile selector chooses the
  same pair as the point best in the cross-matrix and a near-identical pair in
  the split-half. Cross-matrix regret remains 8.0/5.0 tasks and top-3 remains
  0.0; split-half regret is 2.46/2.29 tasks vs 2.37/2.28 baseline. The lower
  bound is not a different selector at these task counts.
- **Prior shrinkage improves the estimate, not the selection.** At λ=0.25 the
  union MAE falls from 0.1056/0.0891 to 0.0937/0.0792, but the split-half top-3
  falls from 0.106/0.098 to 0.046/0.044. On the target with the source prior,
  λ=0.25 matches the target-only exact header (0.000 regret, 1.0 top-3) but
  cannot improve it; λ≥0.5 degrades. The prior is a regularizer for the union
  estimate, not a transfer selector.
- **The exact header's within-matrix exactness is not a transfer rule.** The
  cross-matrix source→target selection is still 5–8 tasks below the target
  oracle with top-3 0.0. The calibration does not rescue it; it confirms the
  boundary.
- **The target-only exact header is the upper bound.** If the target matrix is
  fully observed, the exact header is exact on it; a source prior is redundant.
  A prior can only help when the target is partially observed or when the task
  families share a stable pair structure. The current data do not show that.

**Top number:** **no transfer improvement — robust cross-matrix regret 8.0/5.0
tasks and top-3 0.0, identical to baseline; prior split-half top-3 0.046/0.044
at λ=0.25 vs 0.106/0.098 baseline; the target-only exact header is already
0.000 regret / 1.0 top-3.**

## 5. What changes for V3

- Report the calibration as a **negative** result: robust lower-bound selection
  and simple prior shrinkage do not improve cross-matrix transfer at these task
  counts. The exact header remains a within-matrix storage/query artifact, not
  a transfer selector.
- The prior's MAE improvement is an **estimator** result, not a selection
  result. Do not report it as a transfer win.
- The target-only exact header is the upper bound when the target is fully
  observed; any transfer prior must be evaluated on a **partially observed**
  target (a small target training split) to have a chance to help.
- The negative boundary is now sharper: the failure is not just “the source
  pair is not the target pair”; it survives a robust lower bound and a
  source-prior shrinkage. That is a stronger, more honest claim.

## 6. Limitations

- The split-half uses the **common 12-config** matrices, not the full 14×60 and
  12×80 matrices; the absolute regret values (2.37/2.28 tasks) differ from the
  full-matrix split-half (1.91/1.70 tasks) because the config set changes.
- The robust rule uses the 10th percentile; a 2.5th percentile or a formal
  lower confidence bound could differ. The 10th percentile is the requested
  criterion.
- The prior is a simple convex combination; a hierarchical or task-feature
  prior could behave differently. The current test is the simplest transfer
  prior.
- The prior-target rows are within-target selections, not strict source→target
  selections; the strict source→target prior would leak the target labels.
- The split-half bootstrap uses B=500 splits and B=300 task bootstraps; the CIs
  are Monte Carlo intervals, not exact.
- No scored run, server, lock, GPU, new session, or commit.

## 7. Reproducibility

- `transfer_calibration.py` — rules, split-half, cross-matrix, prior shrinkage.
- `transfer_calibration_results.json` — all values.
- `harness/architect/data/paired.csv` — source matrix; SHA-256
  `51a6fd00c719301b49f256da7771ce12bd7969c1a474473123d3593634bfd180`.
- No scored run, server, lock, GPU, new session, or commit.

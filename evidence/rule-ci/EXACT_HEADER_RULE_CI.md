# Exact-header rule CI: bootstrap intervals and rule certificate

**Rule:** `EXACT-HEADER-PAIR-01`.
**Status:** analysis-only. No scored run, server, lock, GPU, new session, or
commit.
**Data:** 14×60 HumanEval heldout and 12×80 fresh dev matrices reconstructed
from `harness/architect/data/paired.csv` (SHA-256
`51a6fd00c719301b49f256da7771ce12bd7969c1a474473123d3593634bfd180`).
**Reproduce:** `exact_header_rule_ci.py` → `exact_header_rule_ci_results.json`.

## 1. Rule and data

The exact header stores each configuration's pass set as a bitset: 8 bytes for
60 tasks, 10 bytes for 80. Pair union is the bitwise OR; the selection rule is
“choose the pair with the maximum union; ties by smaller total size, then
lexicographic config order.” The rule is exact for the observed task set by
construction: the header contains the full pass set, so the selected pair is the
true best-union pair and the within-sample regret is zero.

The 14×60 matrix has best fixed 36/60, oracle union 43/60, best pair
`q3km_code_kvq8_0_preplus` + `mx_q4km_code_attnq_q5k_plus` = 41/60. The 12×80
matrix has best fixed 49/80, union 58/80, best pair `mx2_aq6_q3ks_plus` +
`mx_q3km_code_gateup_q4k_plus` = 56/80.

## 2. Methods

- **Alpha:** 0.05.
- **Seed:** 20261109.
- **Bootstrap replicates:** B=2,000 for the task and config bootstraps; the
  split-half uses 2,000 random 50/50 splits × 2 directions = 4,000 half
  evaluations.
- **CI method:** percentile (2.5th, 97.5th).
- **Task bootstrap:** resample tasks with replacement, rebuild the exact header,
  recompute the pair metrics. This is the within-sample task-sampling
  uncertainty.
- **Config bootstrap:** resample configurations with replacement, keep distinct
  original configs, rebuild the pair set, recompute the metrics and the
  best-pair union. This is the config-sampling uncertainty.
- **Split-half out-of-sample:** split the tasks 50/50; select the pair on one
  half using the exact header; evaluate on the other half. Metrics: test-half
  regret (test best union − selected pair's test union), union MAE
  (mean |train-half union − test-half union| over all pairs), and top-3 (is the
  test-half best pair in the train-half top-3?).

## 3. Results

### 3.1 Within-sample exactness

| Matrix | Best fixed | Union | Best pair union | Regret | Union MAE | Top-3 |
|---|---:|---:|---:|---:|---:|---:|
| 14×60 | 36/60 | 43/60 | 41/60 | 0.00 | 0.00 | 1.00 |
| 12×80 | 49/80 | 58/80 | 56/80 | 0.00 | 0.00 | 1.00 |

The task and config bootstrap CIs are degenerate:

| Matrix | Task-bootstrap 95% CI (regret / MAE / top-3) | Config-bootstrap 95% CI (regret / MAE / top-3) | Coverage |
|---|---|---|---|
| 14×60 | [0,0] / [0,0] / [1,1] | [0,0] / [0,0] / [1,1] | 100% |
| 12×80 | [0,0] / [0,0] / [1,1] | [0,0] / [0,0] / [1,1] | 100% |

This is not an empirical stability result; it is exactness by construction. The
exact header cannot have a nonzero within-sample regret or MAE, and its top-3
recall is 1.0. The bootstrap confirms the invariance, not the generalization.

### 3.2 Config-stability (config bootstrap): the best pair is not stable

**Config-stability (config bootstrap, not split-half).** The config bootstrap
gives a non-degenerate interval for the **best-pair union**, because resampling
configurations changes which pair is best:

| Matrix | Best-pair union mean [95% CI] | Top pair frequency |
|---|---|---:|
| 14×60 | 39.72 [37, 41] | 40.5% |
| 12×80 | 54.84 [52, 56] | 41.1% |

The top pair is the full-matrix best pair in only 40.5% (heldout) and 41.1%
(fresh) of config resamples. The within-sample regret is still zero in each
resample, but the **identity** of the selected pair is unstable across
configuration sets. A config-level claim such as “the header selects the best
pair” is true only relative to the observed config set; it is not stable under
config resampling.

### 3.3 Split-half out-of-sample

The split-half is the meaningful generalization test: select the pair on half
the tasks, evaluate on the other half.

| Matrix | Regret mean [95% CI] | Regret < 1 task | Union MAE mean [95% CI] | MAE rate | Rate < 0.03 | Top-3 mean [95% CI] | Top-3 ≥ 0.90 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 14×60 | 1.91 [0, 6] | 15.7% | 3.00 [1.15, 7.40] | 0.100 | 0.15% | 0.208 [0, 1] | 20.8% |
| 12×80 | 1.70 [0, 4] | 25.4% | 3.47 [1.00, 8.97] | 0.087 | 6.0% | 0.079 [0, 1] | 7.9% |

**Split-half summary (the numbers to quote, separate from config stability):**

| Matrix | Regret | Union MAE [95% CI] | Top-3 [95% CI] |
|---|---:|---|---|
| 14×60 | 1.91 tasks | 3.00 tasks [1.15, 7.40] | 0.208 [0, 1] |
| 12×80 | 1.70 tasks | 3.47 tasks [1.00, 8.97] | 0.079 [0, 1] |

The out-of-sample bars are not met. The selected pair's test-half union is 1.7–
1.9 tasks below the test-half best; the union estimate error is 3.0–3.5 tasks
(0.087–0.100 rate); the test-half best pair is in the train-half top-3 only
20.8% (14×60) and 7.9% (12×80) of the time. The exact header is exact for the
observed pass set, but the **pair-selection rule** does not generalize to a new
task sample at the observed task counts.

## 4. Rule certificate

The certificate is content-addressed; the full JSON is in
`exact_header_rule_ci_results.json`. Key fields:

```json
{
  "rule_id": "EXACT-HEADER-PAIR-01",
  "version": "1.0",
  "date": "2026-11-09",
  "alpha": 0.05,
  "seed": 20261109,
  "B": 2000,
  "ci_method": "percentile",
  "coverage": {
    "heldout_task_bootstrap": 1.0,
    "heldout_config_bootstrap": 1.0,
    "fresh_task_bootstrap": 1.0,
    "fresh_config_bootstrap": 1.0,
    "heldout_split_half_top3": 0.20775,
    "fresh_split_half_top3": 0.079,
    "heldout_split_half_regret_lt1": 0.15725,
    "heldout_split_half_mae_rate_lt003": 0.0015,
    "heldout_split_half_top3_ge09": 0.20775,
    "fresh_split_half_regret_lt1": 0.254,
    "fresh_split_half_mae_rate_lt003": 0.06,
    "fresh_split_half_top3_ge09": 0.079
  },
  "scope": "Within-sample exactness is by construction; the 50/50 split-half is the out-of-sample estimate. The out-of-sample bars (<1 task regret, <0.03 MAE rate, >=0.90 top-3) are not met.",
  "data_sha256": "51a6fd00c719301b49f256da7771ce12bd7969c1a474473123d3593634bfd180",
  "certificate_sha256": "407f9587c57c99d7a68b90fc741b0ac11559817ce0642df19bc03f4fbbcd8273"
}
```

The certificate's within-sample coverage is 100% by construction. The
out-of-sample bar coverage is the split-half rates above: regret <1 task in
15.7%/25.4% of half evaluations, MAE rate <0.03 in 0.15%/6.0%, top-3 ≥0.90 in
20.8%/7.9%.

## 5. Verdict and top number

**Verdict:** the exact header is exact **within-sample** (0.00-task regret,
0.00 union MAE, 1.00 top-3; degenerate 95% CIs; 100% coverage by construction),
but it is **not exact out-of-sample**. The 50/50 split-half gives 1.91/1.70-task
regret, 3.00/3.47-task union MAE (0.100/0.087 rate), and 0.208/0.079 top-3 on
the 14×60/12×80 matrices. The out-of-sample bars (<1 task regret, <0.03 MAE
rate, ≥0.90 top-3) are not met. The 8-byte/10-byte header is a valid exact
storage artifact for the observed pass set; the pair-selection rule is overfit
to the observed task sample.

**Top number:** **0.00-task pair-selection regret and 0.00 union MAE
within-sample; 0.208 top-3 out-of-sample on 14×60 (0.079 on 12×80), with 1.91/
1.70-task regret.** The within-sample zero is a construction, not a
generalization.

## 6. What changes for the paper

- The exact-header claim should be scoped: “0.00 within-sample regret/MAE on
  the observed pass set” is exact by construction; it is not an out-of-sample
  selection guarantee. The paper should report the split-half top-3 (0.208/0.079; CI [0,1]), the
  split-half union MAE (3.00/3.47 tasks; CIs [1.15,7.40]/[1.00,8.97]), and,
  separately, the config-stability frequency (40.5%/41.1%) from the config
  bootstrap. These are different resampling units.
- The 8-byte header is still a genuine storage result: it is smaller than any
  sketch and exact for the observed pass set. The value is in the **storage and
  query** of the observed behavior, not in a universal pair-selection rule.
- A deployment claim needs a task-diverse calibration or a prior/shrinkage on
  the pair union; the current rule selects the observed best pair but not the
  population best pair. The rule certificate should be attached to the claim,
  with the split-half bars and the config-bootstrap frequency.
- The certificate's alpha (0.05), seed (20261109), B (2,000), and coverage are
  reported; the certificate hash is
  `407f9587c57c99d7a68b90fc741b0ac11559817ce0642df19bc03f4fbbcd8273`.

## 7. What remains unproved

- **Out-of-sample generalization.** The split-half is a 50/50 task split on the
  same benchmark; a larger task suite and a cross-family check are needed. The
  split-half already shows a large gap, so the burden is on the rule.
- **Config-set stability.** The best-pair identity changes across config
  resamples (top pair frequency 40.5%/41.1%); a config-level calibration is
  needed before a model-zoo claim.
- **Task-family shift.** The 14×60 and 12×80 matrices are HumanEval/MBPP; the
  pass-set structure may not transfer to other code families or agentic tasks.
- **The within-sample zero is not evidence of generalization.** It is a
  construction; the bootstrap CI is degenerate for that reason.

## 8. Reproducibility

- `exact_header_rule_ci.py` — rule, bootstrap, split-half, certificate.
- `exact_header_rule_ci_results.json` — all values and the certificate.
- `harness/architect/data/paired.csv` — source matrix; SHA-256
  `51a6fd00c719301b49f256da7771ce12bd7969c1a474473123d3593634bfd180`.
- No scored run, server, lock, GPU, new session, or commit.

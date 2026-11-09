# Cross-matrix out-of-sample test: exact-header pair selection

**Rule:** `EXACT-HEADER-CROSS-01`.
**Status:** analysis-only. No scored run, server, lock, GPU, new session, or
commit.
**Data:** 14×60 HumanEval heldout and 12×80 fresh dev matrices from
`harness/architect/data/paired.csv` (SHA-256
`51a6fd00c719301b49f256da7771ce12bd7969c1a474473123d3593634bfd180`).
**Reproduce:** `cross_matrix_oos.py` → `cross_matrix_oos_results.json`.

## 1. Design and the config-overlap constraint

The exact header is an 8-byte bitset for 60 tasks and 10 bytes for 80; pair
union is the bitwise OR. The cross-matrix test selects the best pair on one
matrix and evaluates its union, regret, and top-3 on the other, against the
other matrix's oracle pair.

The full 14×60 best pair is `q3km_code_kvq8_0_preplus` +
`mx_q4km_code_attnq_q5k_plus` (41/60). The first config is absent from the
12×80 matrix, so the **full** pair cannot be evaluated on 12×80. The valid
cross-matrix test uses the **12 common configs** present in both matrices:

`q3km_none_plus`, `q4km_code_plus`, `q4ks_code_plus`, `q3km_code_preplus`,
`q3km_code_plus`, `mx_q3km_code_attnq_q5k_plus`,
`mx_q3km_code_gateup_q4k_plus`, `mx2_aq5_q3ks_plus`, `mx2_aq6_q3ks_plus`,
`mx2_aq5_attnk5_plus`, `mx_q4km_code_attnq_q5k_plus`, `q3ks_code_plus`.

On the common configs, the 14×60 **common-config oracle** is
`q3km_code_preplus` + `mx_q4km_code_attnq_q5k_plus` (39/60); the 12×80 oracle
is `mx2_aq6_q3ks_plus` + `mx_q3km_code_gateup_q4k_plus` (56/80).

**Metrics.** Regret = target oracle union − selected pair's target union.
Union MAE rate = mean |source union/60 − target union/80| over all 66 pairs
(the rate scale is comparable across the 60- and 80-task matrices). Top-3 = is
the target oracle pair in the source matrix's top-3 by union?

## 2. Point results

| Direction | Selected pair (source) | Source union | Target oracle | Target oracle union | Selected target union | Regret | Union MAE rate | Top-3 |
|---|---|---|---:|---|---:|---:|---:|---:|---:|
| 14×60 → 12×80 | `q3km_code_preplus` + `mx_q4km_code_attnq_q5k_plus` | 39/60 (common-config oracle) | `mx_q3km_code_gateup_q4k_plus` + `mx2_aq6_q3ks_plus` | 56/80 | 48/80 | **8.0 tasks** | **0.0630** | **0.0** |
| 12×80 → 14×60 | `mx_q3km_code_gateup_q4k_plus` + `mx2_aq6_q3ks_plus` | 56/80 | `q3km_code_preplus` + `mx_q4km_code_attnq_q5k_plus` | 39/60 (common-config oracle) | 34/60 | **5.0 tasks** | **0.0630** | **0.0** |

The cross-matrix selection is 5–8 tasks below the target oracle, and the target
oracle is not in the source top-3 in either direction. The union MAE rate is
0.063, above the 0.03 bar. The 8-byte header is exact **within** each matrix; it
does not select the other matrix's best pair.

## 3. Bootstrap CIs

Each bootstrap uses B=2,000 replicates and percentile 95% CIs. “Combined”
resamples source tasks, target tasks, and configs together; “source” resamples
source tasks and reselects; “target” fixes the full-source selection and
resamples target tasks; “config” resamples the 12 common configs and reselects.

### 3.1 14×60 → 12×80

| Bootstrap | Regret mean [95% CI] | Union MAE rate mean [95% CI] | Top-3 mean [95% CI] |
|---|---:|---:|---:|
| Combined | 5.249 [0, 13] | 0.0894 [0.0312, 0.2115] | 0.095 [0, 1] |
| Source tasks | 6.559 [2, 8] | 0.0783 [0.0324, 0.1748] | 0.003 [0, 0] |
| Target tasks | 8.539 [3, 15] | 0.0743 [0.0310, 0.1555] | 0.002 [0, 0] |
| Configs | 5.719 [1, 8] | 0.0630 [0.0436, 0.0839] | 0.020 [0, 0] |

### 3.2 12×80 → 14×60

| Bootstrap | Regret mean [95% CI] | Union MAE rate mean [95% CI] | Top-3 mean [95% CI] |
|---|---:|---:|---:|
| Combined | 4.447 [0, 11] | 0.0879 [0.0311, 0.1987] | 0.106 [0, 1] |
| Source tasks | 4.641 [2, 6] | 0.0742 [0.0310, 0.1508] | 0.000 [0, 0] |
| Target tasks | 5.805 [1, 12] | 0.0778 [0.0318, 0.1745] | 0.021 [0, 0] |
| Configs | 3.888 [1, 6] | 0.0634 [0.0435, 0.0850] | 0.036 [0, 1] |

The bootstrap intervals confirm the point result: the lower bound of the union
MAE rate is ~0.031–0.044, above or at the 0.03 bar; the top-3 rate is 0.00–0.11,
far below the 0.90 bar; the regret intervals exclude the <1-task bar in most
resamples. The combined top-3 CI is [0,1] because top-3 is binary, but the mean
is 0.095/0.106, not 0.90.

## 4. Rule certificate

```json
{
  "rule_id": "EXACT-HEADER-CROSS-01",
  "version": "1.0",
  "date": "2026-11-09",
  "alpha": 0.05,
  "seed": 20261109,
  "B": 2000,
  "ci_method": "percentile",
  "common_configs": [
    "q3km_none_plus", "q4km_code_plus", "q4ks_code_plus", "q3km_code_preplus",
    "q3km_code_plus", "mx_q3km_code_attnq_q5k_plus",
    "mx_q3km_code_gateup_q4k_plus", "mx2_aq5_q3ks_plus",
    "mx2_aq6_q3ks_plus", "mx2_aq5_attnk5_plus",
    "mx_q4km_code_attnq_q5k_plus", "q3ks_code_plus"
  ],
  "full_14x60_best_pair": ["q3km_code_kvq8_0_preplus", "mx_q4km_code_attnq_q5k_plus"],
  "full_14x60_missing_from_12x80": ["q3km_code_kvq8_0_preplus"],
  "scope": "Cross-matrix test on the 12 common configs. The full 14x60 best pair is not evaluable on 12x80 because one config is absent.",
  "data_sha256": "51a6fd00c719301b49f256da7771ce12bd7969c1a474473123d3593634bfd180",
  "certificate_sha256": "6c045220bf7b4a73cafd363ecbdec8b046255bab0e5ebfa5c7ae6a86b551f320"
}
```

## 5. Verdict and top number

**Verdict: the cross-matrix out-of-sample test fails.** The exact header selects
the source matrix's best pair, but that pair is 8.0 tasks below the 12×80 oracle
when moving 14×60 → 12×80, and 5.0 tasks below the 14×60 oracle when moving
12×80 → 14×60. On the full matrices, the target oracle is not in the source top-3 (point
top-3 = 0.0 in both directions; combined bootstrap mean 0.095/0.106, still far
below the 0.90 bar). The union MAE rate is 0.063, above the 0.03 bar; the
bootstrap lower bounds are 0.031–0.044. The 8-byte
header is an exact storage artifact for the observed pass set, but the pair
selection does not transfer across task matrices.

**Top number:** **0.0 point top-3 in both directions (combined bootstrap mean
0.095/0.106, still far below 0.90); 8.0/5.0-task regret; 0.063 union MAE rate.** The full 14×60 best pair (41/60) is not evaluable on 12×80 because
`q3km_code_kvq8_0_preplus` is absent; the common-config pair (39/60) is the valid
cross-matrix selection.

## 6. What changes for V3

- The V3 claim must be scoped: “the exact header is exact for the observed pass
  set” is supported; “the exact header selects the best pair on a new task
  matrix” is **not** supported. The independent out-of-sample evidence is
  negative.
- The 8-byte header remains a real storage/query artifact: it is smaller than
  any sketch and exact for the matrix it was built on. The value is in the
  storage and the observed-matrix query, not in a universal pair-selection rule.
- A deployment claim needs a task-diverse calibration, a prior/shrinkage on the
  pair union, or an ensemble across task families. The current rule is a
  within-matrix selector.
- The full 14×60 best pair includes a config absent from 12×80; any cross-matrix
  claim must either restrict to the common configs (as done here) or add the
  missing config to the target matrix. The full-pair test is not identifiable
  with the current artifacts.

## 7. What remains unproved

- **Task-family transfer.** The 14×60 heldout and 12×80 dev matrices are
  HumanEval/MBPP; a third family or agentic suite is needed. The current result
  is already negative, so the burden is on the rule.
- **Config-set transfer.** The 12 common configs are a subset; the full 14×60
  best pair is not evaluable on 12×80. A matched config set on both matrices is
  needed for a clean full-pair test.
- **Calibration.** A task-diverse prior or shrinkage could improve the
  cross-matrix selection; this is a new hypothesis, not a result.
- **The within-matrix exactness is not out-of-sample evidence.** The 0.00
  within-matrix regret is a construction; the cross-matrix result is the
  independent test.

## 8. Reproducibility

- `cross_matrix_oos.py` — selection, evaluation, bootstraps, certificate.
- `cross_matrix_oos_results.json` — all values and the certificate.
- `harness/architect/data/paired.csv` — source matrix; SHA-256
  `51a6fd00c719301b49f256da7771ce12bd7969c1a474473123d3593634bfd180`.
- No scored run, server, lock, GPU, new session, or commit.

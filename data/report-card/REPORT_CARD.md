# Behavioral report card — 14 Qwen configs

**Scope:** 14 Qwen2.5-Coder-1.5B configurations x 60 HumanEval heldout tasks. Exact pass-set headers from the repository-backed evidence manifest; no new run.

**Baseline:** `q3km_code_kvq8_0_preplus` (36/60 = 60.0%). **Oracle union:** 43/60 = 71.7%.

**Regression flags:** `severe_regression` = lost >=5 baseline passes and net <0; `regression` = lost > gained; `neutral` = lost == gained; `improvement` = gained > lost.

## 1. Per-config report card

| Config | MiB | Pass | Rate | Unique | + vs base | - vs base | Net | Flag | Best partner | Union | Compl. |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|
| `q3km_code_kvq8_0_preplus` | 786.00 | 36/60 | 60.0% | 0 | 0 | 0 | +0 | baseline | `mx_q4km_code_attnq_q5k_plus` | 41/60 | 5 |
| `q3km_code_preplus` | 786.00 | 33/60 | 55.0% | 0 | 0 | 3 | -3 | regression | `mx_q4km_code_attnq_q5k_plus` | 39/60 | 6 |
| `mx2_aq5_attnk5_plus` | 804.95 | 31/60 | 51.7% | 0 | 2 | 7 | -5 | severe_regression | `q3km_code_kvq8_0_preplus` | 38/60 | 2 |
| `mx_q3km_code_attnq_q5k_plus` | 802.24 | 31/60 | 51.7% | 0 | 3 | 8 | -5 | severe_regression | `q3km_code_kvq8_0_preplus` | 39/60 | 3 |
| `mx_q4km_code_attnq_q5k_plus` | 948.24 | 31/60 | 51.7% | 1 | 5 | 10 | -5 | severe_regression | `q3km_code_kvq8_0_preplus` | 41/60 | 5 |
| `q3km_code_plus` | 786.00 | 31/60 | 51.7% | 0 | 2 | 7 | -5 | severe_regression | `q4km_code_preplus` | 38/60 | 7 |
| `q3ks_code_plus` | 725.69 | 31/60 | 51.7% | 0 | 2 | 7 | -5 | severe_regression | `q4km_code_preplus` | 38/60 | 7 |
| `q4km_code_preplus` | 940.37 | 31/60 | 51.7% | 0 | 2 | 7 | -5 | severe_regression | `q3km_code_plus` | 38/60 | 7 |
| `mx2_aq5_q3ks_plus` | 741.94 | 30/60 | 50.0% | 0 | 1 | 7 | -6 | severe_regression | `q4km_code_preplus` | 37/60 | 6 |
| `mx2_aq6_q3ks_plus` | 750.30 | 30/60 | 50.0% | 0 | 2 | 8 | -6 | severe_regression | `q3km_code_kvq8_0_preplus` | 38/60 | 2 |
| `q4km_code_plus` | 940.37 | 30/60 | 50.0% | 0 | 4 | 10 | -6 | severe_regression | `q3km_code_kvq8_0_preplus` | 40/60 | 4 |
| `mx_q3km_code_gateup_q4k_plus` | 883.62 | 28/60 | 46.7% | 0 | 3 | 11 | -8 | severe_regression | `q3km_code_kvq8_0_preplus` | 39/60 | 3 |
| `q4ks_code_plus` | 896.75 | 28/60 | 46.7% | 0 | 2 | 10 | -8 | severe_regression | `q3km_code_kvq8_0_preplus` | 38/60 | 2 |
| `q3km_none_plus` | 786.00 | 25/60 | 41.7% | 0 | 1 | 12 | -11 | severe_regression | `q3km_code_kvq8_0_preplus` | 37/60 | 1 |

## 2. Pairwise complementarity — top 10

| Pair | Union | Union % | Complementarity | Jaccard | Unique A | Unique B |
|---|---:|---:|---:|---:|---:|---:|
| `q3km_code_kvq8_0_preplus` + `mx_q4km_code_attnq_q5k_plus` | 41/60 | 68.3% | 5 | 0.634 | 10 | 5 |
| `q4km_code_plus` + `q3km_code_kvq8_0_preplus` | 40/60 | 66.7% | 4 | 0.650 | 4 | 10 |
| `q3km_code_preplus` + `mx_q4km_code_attnq_q5k_plus` | 39/60 | 65.0% | 6 | 0.641 | 8 | 6 |
| `q3km_code_kvq8_0_preplus` + `mx_q3km_code_attnq_q5k_plus` | 39/60 | 65.0% | 3 | 0.718 | 8 | 3 |
| `q3km_code_kvq8_0_preplus` + `mx_q3km_code_gateup_q4k_plus` | 39/60 | 65.0% | 3 | 0.641 | 11 | 3 |
| `q4km_code_preplus` + `mx_q3km_code_attnq_q5k_plus` | 38/60 | 63.3% | 7 | 0.632 | 7 | 7 |
| `q4km_code_preplus` + `q3km_code_plus` | 38/60 | 63.3% | 7 | 0.632 | 7 | 7 |
| `q4km_code_preplus` + `q3ks_code_plus` | 38/60 | 63.3% | 7 | 0.632 | 7 | 7 |
| `q4km_code_plus` + `q3km_code_preplus` | 38/60 | 63.3% | 5 | 0.658 | 5 | 8 |
| `q3km_code_kvq8_0_preplus` + `mx2_aq5_attnk5_plus` | 38/60 | 63.3% | 2 | 0.763 | 7 | 2 |

## 3. Regression audit

| Config | Lost vs baseline | Gained vs baseline | Net | Flag |
|---|---:|---:|---:|---|
| `q3km_none_plus` | 12 | 1 | -11 | severe_regression |
| `mx_q3km_code_gateup_q4k_plus` | 11 | 3 | -8 | severe_regression |
| `mx_q4km_code_attnq_q5k_plus` | 10 | 5 | -5 | severe_regression |
| `q4km_code_plus` | 10 | 4 | -6 | severe_regression |
| `q4ks_code_plus` | 10 | 2 | -8 | severe_regression |
| `mx2_aq6_q3ks_plus` | 8 | 2 | -6 | severe_regression |
| `mx_q3km_code_attnq_q5k_plus` | 8 | 3 | -5 | severe_regression |
| `mx2_aq5_attnk5_plus` | 7 | 2 | -5 | severe_regression |
| `mx2_aq5_q3ks_plus` | 7 | 1 | -6 | severe_regression |
| `q3km_code_plus` | 7 | 2 | -5 | severe_regression |
| `q3ks_code_plus` | 7 | 2 | -5 | severe_regression |
| `q4km_code_preplus` | 7 | 2 | -5 | severe_regression |
| `q3km_code_preplus` | 3 | 0 | -3 | regression |

## 4. Certificate summary

- Rule certificate `EXACT-HEADER-01`: **SUCCESS**.
- Claims: {'SUPPORTED': 3, 'SUPPORTED_SECONDARY': 2, 'CORRECTED': 1, 'SUPPORTED_SCOPE': 1}; orphan claims: [].
- Heldout task-list SHA-256: `a5e68d95e7adf158d7b0617a154aff68c714ca2a9008343980c6a0af07bcff3f`.

## 5. Example insight

Best pair q3km_code_kvq8_0_preplus + mx_q4km_code_attnq_q5k_plus reaches 41/60 (68.3%), 5 tasks above the best single. The complement mx_q4km_code_attnq_q5k_plus passes 31/60, but only 5 of those passes are outside the baseline; the pair gain is 5, not the complement's total pass count.

## 6. Reproduce

```
python harness/architect/queue/report-card-demo/report_card.py
```


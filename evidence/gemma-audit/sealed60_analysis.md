# Gemma sealed-60 MBPP panel — analysis

Panel: `GEM-SEALED60-01`; n=60; invalid=False.
Single passes: {'q3_mix': 36, 'gp1_qat_requant': 35, 'google_qat_q4_0': 40, 'udq4_k_xl': 40}.

| Pair | Union | Unsloth | Gain | b | c | one-sided p | two-sided p | 95% CI | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `q3_mix+gp1_qat_requant` | 40/60 | 40/60 | +0 | 4 | 4 | 0.6367 | 1.0000 | (-6, 6) | FAILURE |
| `q3_mix+google_qat_q4_0` | 42/60 | 40/60 | +2 | 4 | 2 | 0.3438 | 0.6875 | (-3, 7) | INCONCLUSIVE |
| `q3_mix+udq4_k_xl` | 43/60 | 40/60 | +3 | 3 | 0 | 0.1250 | 0.2500 | (0, 7) | INCONCLUSIVE |

**Rule:** success if pair union ≥ Unsloth +1 and exact one-sided McNemar p<0.10; failure if union ≤ Unsloth; otherwise inconclusive.

**Size caveat:** Unsloth UD-Q4 is 2,498.98 MiB; the team pair is 5,432.83 MiB (2.17x). A pass-count win is not a size-matched win.

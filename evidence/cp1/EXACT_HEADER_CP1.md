# Exact-header certified pass@1 and selection certificate

**Date:** 2026-11-09
**Status:** analysis-only. No scored run, server, eval lock, GPU work, new session, or
commit. The numbers are derived from the existing 14×60 and 12×80 pass-set matrices and
from `CP1_FEASIBILITY.md`.
**Inputs:** `CP1_FEASIBILITY.md`; `analysis/cp1_feasibility_results.json`;
`harness/architect/agents/04_routing/pass_set_sketch_output.json`; `pass_set_sketch.py`;
`PASS_SET_SKETCH_FEASIBILITY.md`; `harness/architect/agents/10_literature/SYNTHESIS_PAPER_OUTLINE.md`.

## 0. Definitions and protocol

- **CP@1 (certified pass@1).** The false-pass-adjusted lower bound
  \[
  \mathrm{CP@1}=\frac{1}{N}\sum_i y_i\,s_i,
  \]
  where \(y_i\) is the visible pass and \(s_i=P(\text{hidden pass}\mid\text{visible pass})\).
  The global certificate uses the pooled false-pass rate; the LOO variant estimates
  \(s_i\) from the other configurations. The measured certificate rates are:
  - eight saved configs: **18/269 = 6.69%** false-pass, exact 95% CI **[4.01%, 10.37%]**;
  - nine-config reference incl. F16: **21/305 = 6.89%** [4.31%, 10.33%];
  - private 202-mutant set: **202/202 killed**, score lower bound **0.982**.
  CP@1 is **within-sample/matrix-level**; it is not an out-of-sample guarantee and it is
  not conformal coverage.
- **Selection coverage.** The fraction of 200 hash seeds where the selected pair equals the
  true best pair (top-1 selection). This is the **selection certificate** metric, not CP@1.
  The exact header's selection coverage is 1.000 by construction.
- **Selection certificate.** A record with method, header size, calibration split, test
  split, α, selection coverage + exact 95% CI, regret + Rule CI (2.5/97.5 seed percentiles),
  union MAE + Rule CI, top-3, both-bars fraction, and verdict. It verifies if the **test**
  selection coverage 95% CI lower is ≥1−α and the union MAE is ≤0.03.
- **α:** 0.05 and 0.10. **Calibration split:** 14×60 heldout. **Test split:** 12×80 fresh.
- **Headers:** exact 8/10-byte pass-set bitset; MinHash-512 at 2,048 B (uint32); Bloom-512
  at 64 B; Bloom-64 at 8 B.

## 1. CP@1 values

**Exact 8/10-byte header.** The selected pair's union is 41/60 = **0.6833** on 14×60 and
56/80 = **0.7000** on 12×80. The false-pass certificate is 18/269 = 6.69% [4.01, 10.37].
CP@1 = 0.6833 × (1 − 0.0669) = **0.6376** on 14×60 and 0.7000 × (1 − 0.0669) =
**0.6532** on 12×80. The conservative joint 95% interval (pair-union exact CI × false-pass
exact CI) is **[0.491, 0.764]** and **[0.524, 0.763]**. The certified pass@1 lower-bound
coverage is **1.000 [0.982, 1.000]** within-sample; this is the coverage of the certified
bound, not a conformal guarantee and not an out-of-sample result. The selection coverage
(top-1 pair = true best) is separate: **1.000**.

**Eight saved configs (global certificate, 18/269 = 6.69%):**

| Config | CP@1 [95% CI] | LOO CP@1 |
|---|---|---|
| `q3km_code` | 0.5443 [0.4257, 0.6641] | 0.5406 |
| `q3km_code_kv8` | **0.5910 [0.4750, 0.7070]** | **0.5906** |
| `q4km_code` | 0.5132 [0.3957, 0.6355] | 0.5073 |
| `q5ks_none` | 0.5443 [0.4225, 0.6639] | 0.5406 |
| `q8_0_none` | 0.5443 [0.4234, 0.6653] | 0.5406 |
| `q3km_none` | 0.4199 [0.2988, 0.5463] | 0.4286 |
| `q4ks_code` | 0.4821 [0.3602, 0.6086] | 0.4925 |
| `q5km_none` | 0.5443 [0.4235, 0.6635] | 0.5425 |

The nine-config reference certificate is 21/305 = 6.89% [4.31%, 10.33%]; the CP@1 values
are 0.2 pp lower. The private 202/202 certificate has a lower bound of 0.982. All values
are within-sample/matrix-level; the false-pass rate is measured on the same 60-task matrix.

**MinHash-512 selected pair union.** 14×60: 41.0/60 = 0.6833; CP@1 = **0.6376**,
conservative 95% interval **[0.491, 0.764]**. 12×80: 55.955/80 = 0.6994; CP@1 =
**0.6526**, conservative 95% interval **[0.524, 0.763]**. The MinHash CP@1 is nearly
identical to the exact header because the selected pair is the same in 100%/96.5% of
seeds; the difference is **selection coverage** (1.000 vs 0.965), not CP@1. The 90% figure
is the selection coverage on the 12×80 test split (0.965), not CP@1.

**Bloom-512 selected pair union (secondary).** 14×60: 40.755/60 = 0.6793; CP@1 =
**0.6338**, conservative 95% interval **[0.488, 0.761]**. 12×80: 55.87/80 = 0.6984; CP@1
= **0.6517**, conservative 95% interval **[0.524, 0.763]**. Bloom's selection coverage is
0.905/0.935; its CP@1 is not a selection certificate.

## 2. Selection certificate

**Selection coverage** (top-1 pair = true best; exact binomial CI over 200 seeds):

| Method | Size | Cal 14×60 selection coverage [95% CI] | Test 12×80 selection coverage [95% CI] | Regret cal/test | MAE cal/test | Top-3 cal/test | Certificate |
|---|---:|---|---|---:|---:|---:|---|
| **Exact 8/10-B** | **8/10 B** | **1.000 [0.982, 1.000]** | **1.000 [0.982, 1.000]** | **0.00/0.00** | **0.00/0.00** | **1.00/1.00** | **PASS at α=0.05 and 0.10** |
| MinHash-512 | 2,048 B | 1.000 [0.982, 1.000] | 0.965 [0.929, 0.986] | 0.00/0.045 | 0.0079/0.0056 | 1.00/0.995 | Cal PASS; test PASS at α=0.10, FAIL at α=0.05 |
| Bloom-512 | 64 B | 0.905 [0.856, 0.942] | 0.935 [0.891, 0.965] | 0.245/0.13 | 0.0222/0.0306 | 0.95/0.945 | FAIL at α=0.05 and 0.10; test MAE >0.03 |
| Bloom-64 | 8 B | 0.145 [0.099, 0.202] | 0.125 [0.083, 0.179] | 2.17/1.855 | 0.0993/0.1269 | 0.47/0.13 | FAIL at both α |

**Rule CI (2.5/97.5 seed percentiles):**

| Method | Regret cal / test | MAE cal / test |
|---|---|---|
| Exact 8/10-B | 0 / 0 | 0 / 0 |
| MinHash-512 | [0, 0] / [0, 1] | [0.228, 0.848] / [0.217, 0.772] |
| Bloom-512 | [0, 4] / [0, 2] | [0.306, 3.182] / [0.378, 4.578] |
| Bloom-64 | [0, 6] / [0, 4] | [1.357, 17.886] / [2.170, 28.274] |

The both-bars fraction is 1.00/1.00 for the exact header, 1.00/0.965 for MinHash-512,
0.71/0.465 for Bloom-512, and 0.03/0.02 for Bloom-64.

## 3. Verdict

**Exact 8/10-byte header — VERIFIES.** The selection certificate verifies at α=0.05 and
0.10: selection coverage 1.000 [0.982, 1.000], regret 0.00, union MAE 0.00. The CP@1 value
is **0.6376/0.6532** for the selected pair (pair union × (1 − 6.69%)), with a certified
pass@1 lower-bound coverage of
1.000 [0.982, 1.000] within-sample. The 8-byte (60-task) and 10-byte (80-task) sizes are
smaller than MinHash-512 (2,048 B) and Bloom-512 (64 B), and exact. This is **not conformal
coverage** and **not an out-of-sample guarantee**.

**MinHash-512 — PARTIAL.** Calibration selection coverage 1.000 [0.982, 1.000]; test
0.965 [0.929, 0.986]. At α=0.05 the test CI lower is below 0.95, so the 95% selection
certificate does not verify; at α=0.10 it does. MinHash-512 is a 90% within-sample fallback,
not an exact header; its CP@1 values are **0.6376/0.6526** (pair union × (1 − 6.69%)), and its selection coverage is 1.000/0.965. The 90% figure is selection coverage on the 12×80 test split, not CP@1.

**Bloom-512 — FAILS.** Selection coverage 0.905 [0.856, 0.942] on calibration and 0.935
[0.891, 0.965] on test; the CI lower bounds are below 0.90, so the certificate does not
verify at α=0.10 or 0.05. The test union MAE is 0.0306, above the 0.03 bar; the both-bars
fraction is 0.465. Bloom-64 fails outright.

## 4. Scope and caveats

- CP@1 is **within-sample/matrix-level**. The false-pass rate is measured on the same
  60-task matrix; it is not an out-of-sample or cross-matrix guarantee. The 50/50
  split-half and cross-matrix results in the V4 input remain the boundary evidence.
- The 1.000 [0.982, 1.000] is the **certified pass@1 lower-bound coverage** for the exact
  header, not conformal coverage. The exact header's CP@1 value is the false-pass-adjusted
  selected pair union (0.6376/0.6532), not 1.000.
- The exact header is valid only for the fixed task taxonomy and task order; it must carry
  the task-list hash and a version. A new task family requires a new header.
- The 14×60 and 12×80 matrices are 60/80-task benchmarks, not a 200–300-task suite. The
  selection coverage is over 200 hash seeds; the CP@1 CIs are exact binomial.
- MinHash-512 is a secondary approximation for large/unbounded task universes; Bloom is not
  competitive for these small pass sets.

## 5. Critique fix and top number

**Critique fix (F3/M1):** the exact 8/10-byte header is a public, compact artifact that can
be released with the task-list hash, config IDs, and a `claim.cert`; the 14×60/12×80
matrices are 60/80-task benchmarks, so the 10-task screen is moot. Publish the exact
headers, the selection certificate JSON, and the exact commands. The CP@1 certificate is a
separate within-sample artifact with the false-pass rates above.

**Top number:** the **exact 8/10-byte header** gives **selection coverage 1.000 (95% CI
0.982–1.000)**, **0.00-task pair-selection regret**, **0.00 union MAE**, and a **certified
pass@1 lower-bound coverage of 1.000 [0.982, 1.000]** within-sample; the CP@1 value for the
selected pair is **0.6376/0.6532** (95% interval [0.491, 0.764]/[0.524, 0.763]); MinHash-512 CP@1 is **0.6376/0.6526**, selection coverage 1.000/0.965; Bloom-512 CP@1 is **0.6338/0.6517**, selection coverage 0.905/0.935. The 90% figure is selection coverage, not CP@1. The false-pass certificate is **18/269 = 6.69%
[4.01%, 10.37%]** (eight configs) / **21/305 = 6.89% [4.31%, 10.33%]** (nine-config
reference); the private 202/202 lower bound is **0.982**. The selection certificate verifies
at α=0.05 and 0.10. MinHash-512 is a 90% within-sample fallback; Bloom-512 fails.

## 6. V4 input patch

The V4 input (`harness/architect/agents/10_literature/PAPER_DRAFT_V4_INPUT.md`) and the V4
draft (`PAPER_DRAFT_V4.md`) are outside this agent's write scope. The exact replacement
text for §3.4 and the CP@1 bar is in `V4_SECTION_3_4_PATCH.md` under this directory; the
lead or the 10_literature owner can apply it. The patch removes "conformal coverage",
reports the false-pass rates, and scopes CP@1 within-sample/matrix-level.

## 7. Reproducibility

```bash
python harness/architect/agents/04_routing/pass_set_sketch.py
python harness/architect/agents/09_benchmark/analysis/cp1_feasibility.py
```

The selection coverage is the `regret_zero_frac` over 200 seeds for the sketch methods;
the exact header is exact by construction. The CP@1 values and false-pass CIs are from
`CP1_FEASIBILITY.md` and `analysis/cp1_feasibility_results.json`. No model, server, lock,
GPU, or scored run.


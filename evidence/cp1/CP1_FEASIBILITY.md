# CP@1 feasibility analysis

**Date:** 2026-11-09
**Status:** analysis-only. No scored run, server, eval lock, GPU work, new session, or
commit. The 480 visible-test executions are CPU-only on saved completions.
**Inputs:** `analysis/verifier_retro_results.json`; `analysis/cp1_feasibility_results.json`;
`harness/team/results/private-eval/verification_summary.json`;
`harness/architect/data/paired.csv`; `harness/data/splits.json`.
**Script:** `analysis/cp1_feasibility.py`.

## 0. Definition and data

For task \(i\), let \(y_i\) be the visible base-test pass and \(s_i=P(\text{hidden pass}\mid
\text{visible pass})\) the test soundness. CP@1 is

\[
\mathrm{CP@1}=\frac{1}{N}\sum_i y_i\,\hat{s}_i,
\]

with a 95% interval. Two estimators are tested:

- **Global certificate:** \(\hat{s}_i=1-\hat{f}\), where \(\hat{f}\) is the pooled
  false-pass rate across the eight saved configs. This is the certificate a 40-task
  calibration set would estimate.
- **Leave-one-config-out (LOO) certificate:** \(\hat{s}_i\) is estimated for each task from
  the other seven configs' visible/hidden outcomes. This is a proxy for a per-task
  mutation certificate; it tests whether per-task soundness weights can change the ranking.

Data: eight saved compressed configs, 60 HumanEval heldout tasks. Visible = base HumanEval
tests; hidden = full HumanEval+ (`passed`). The lead's 21/305 = 6.9% reference includes
F16; the eight compressed configs alone give **18/269 = 6.69%**, and the nine-config set
(8 + F16) gives **21/305 = 6.89%**. The private 202-mutant set is the high-soundness anchor:
202/202 killed, score 1.0, exact 95% CI [0.9819, 1.0].

## 1. False-pass rate

| Set | False | Visible | Rate | Exact 95% CI |
|---|---:|---:|---:|---|
| Eight saved configs | 18 | 269 | **6.69%** | **[4.01%, 10.37%]** |
| Nine configs incl. F16 | 21 | 305 | 6.89% | [4.31%, 10.33%] |
| Private 202 mutants | 0 survivors | 202 | 0.00% (score 1.0) | [0.00%, 1.81%] failure; score CI [0.9819, 1.0] |

The per-config false-pass rates are 5.26%–9.68% with exact CIs 0.64%–25.75%; the CIs
overlap heavily. The eight-config pooled rate is 6.69% (the lead's 6.9% is the nine-config
reference).

## 2. Per-config CP@1

Global CP@1 = raw visible rate × (1 − 0.0669); global lower bound = raw × (1 − 0.1037).
LOO CP@1 uses the other seven configs' per-task soundness. CIs are 10,000-draw task
bootstraps.

| Config | Visible | Hidden | False | FP rate | Global CP@1 [95% CI] | LOO CP@1 [95% CI] |
|---|---:|---:|---:|---:|---|---|
| `q3km_code` | 35 | 33 | 2 | 5.71% | 0.5443 [0.4257, 0.6641] | 0.5406 [0.4192, 0.6627] |
| `q3km_code_kv8` | 38 | 36 | 2 | 5.26% | **0.5910 [0.4750, 0.7070]** | **0.5906 [0.4733, 0.7081]** |
| `q4km_code` | 33 | 31 | 2 | 6.06% | 0.5132 [0.3957, 0.6355] | 0.5073 [0.3873, 0.6311] |
| `q5ks_none` | 35 | 33 | 2 | 5.71% | 0.5443 [0.4225, 0.6639] | 0.5406 [0.4187, 0.6611] |
| `q8_0_none` | 35 | 33 | 2 | 5.71% | 0.5443 [0.4234, 0.6653] | 0.5406 [0.4184, 0.6629] |
| `q3km_none` | 27 | 25 | 2 | 7.41% | 0.4199 [0.2988, 0.5463] | 0.4286 [0.3071, 0.5548] |
| `q4ks_code` | 31 | 28 | 3 | 9.68% | 0.4821 [0.3602, 0.6086] | 0.4925 [0.3710, 0.6175] |
| `q5km_none` | 35 | 32 | 3 | 8.57% | 0.5443 [0.4235, 0.6635] | 0.5425 [0.4190, 0.6643] |

The top config is `q3km_code_kv8` under raw pass@1, hidden pass@1, global CP@1, the global
lower bound, and LOO CP@1. The raw and hidden top agree.

## 3. Ranking vs raw pass@1

| Comparison | Spearman | Kendall | Interpretation |
|---|---:|---:|---|
| Raw vs hidden | 0.962 | 0.938 | The raw ranking is already close to the hidden ground truth |
| Raw vs global CP@1 | **1.000** | **1.000** | A global certificate is a constant multiplier; the ranking cannot change |
| Raw vs global lower bound | 1.000 | 1.000 | Same constant-multiplier property |
| Raw vs LOO CP@1 | 0.962 | 0.938 | LOO changes the ranking, but in the same direction as raw-vs-hidden |
| LOO vs hidden | 0.850 | 0.760 | The LOO per-task proxy does **not** recover the hidden ranking better than raw |
| Global CP@1 vs hidden | 0.962 | 0.938 | Same as raw vs hidden |

The global CP@1 cannot change the ranking by construction. The LOO certificate changes the
ranking but is *less* aligned with hidden than raw pass@1 (Kendall 0.76 vs 0.938); the
per-task soundness estimated from other configs is too noisy to correct the held-out
config's false passes. The raw ranking is already 0.938 Kendall with hidden; the 6.7%
false-pass rate is too small and too sparse to change the top config.

## 4. Is a 40-task certificate justified?

**No for ranking/config selection; only conditionally as a conservative absolute-rate
check, and even then it is underpowered.**

- At 6.9% false-pass, 40 tasks expect **2.7 false-pass events**. The exact 95% CI for 3/40
  is **[1.6%, 20.4%]**; for 2/40 it is **[0.6%, 16.9%]**. The per-config false-pass rates
  (5.3%–9.7%) have overlapping CIs of 0.6%–25.8%; a 40-task certificate cannot separate
  them.
- A global certificate is a constant multiplier of raw pass@1: the ranking is unchanged
  (Kendall 1.0). A 40-task certificate therefore cannot improve config selection.
- A per-task LOO certificate does change the ranking, but it is less aligned with hidden
  (Kendall 0.76) than raw pass@1 (0.938); the 40-task version would be noisier still.
- The private 202/202 set shows that a high-soundness certificate is possible (score lower
  bound 0.982), but the public base tests are the weak link. Closing that gap needs a
  larger certificate (roughly 100+ tasks) or a per-task mutation certificate with a
  stronger hidden suite, not a 40-task global calibration.

**Verdict:** CP@1 is feasible as a **global lower-bound metric** — the eight-config
certificate is 6.69% false-pass [4.01%, 10.37%], giving a 0.933 multiplier and a 0.896
lower-bound multiplier — but it is **not a ranking fix at 40 tasks**. The 40-task
certificate is **not justified for config selection**; it is justified only as a
conservative absolute-rate check with a wide CI. The 60-task data already shows the raw
ranking is 0.938 Kendall with hidden and the top config is unchanged; the certificate adds
a lower bound, not a reordering.

## 5. What this means for the CP@1 idea

- Keep CP@1 as a **reported lower bound**, not as a ranking method. The benchmark should
  report raw pass@1, hidden pass@1 when available, and the certified lower bound with the
  certificate's CI.
- A 40-task certificate is a **pilot**, not a fix. The minimal defensible certificate is
  100+ tasks or a per-task mutation certificate (10 mutants/task) that estimates test
  strength directly; the 202/202 private set is the high-soundness target.
- The 40-task paired HumanEval+/MBPP+ benchmark (M1) remains the critique fix; CP@1
  supplements it with a soundness certificate, but it does not replace the paired benchmark.

## 6. Reproducibility

```bash
python harness/architect/agents/09_benchmark/analysis/cp1_feasibility.py
```

The script runs 480 visible base-test executions on saved completions, computes the eight
configs' CP@1 with 10,000 task bootstraps, and writes
`analysis/cp1_feasibility_results.json`. No model, server, lock, GPU, or scored run.

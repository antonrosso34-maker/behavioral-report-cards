# CP@1 40-task panel — SUPERSEDED PRE-RUN TEMPLATE (see evidence/cp40/cp40_analysis.md)

**Date:** 2026-11-09
**Status:** SUPERSEDED pre-run template; the completed run is evidence/cp40/cp40_analysis.md, server, eval lock, GPU work,
new session, or commit. The panel is a low-priority V6 transfer test; the 14×60/12×80
matrices remain the primary evidence.
**Bridge source:** `harness/architect/queue/EVIDENCE_MANIFEST_PLAN.md` §7; public manifest
`harness/architect/queue/evidence/pass-set-header/`.
**Related:** `EXACT_HEADER_CP1.md`; `CP1_FEASIBILITY.md`; `V4_SECTION_3_4_PATCH.md`;
`CP40_PREP_REPORT.md`.
**Template JSON:** `analysis/cp1_panel_40_certificate_template.json`.

**Frozen split (2026-11-09T20:18:21Z):** `harness/architect/queue/cp40/cp40_split.json`;
20 HE+ unused + 20 MBPP+ unused; panel 40 SHA-256 `14161ce8…`; Merkle root
`bd1c8f8a…`; remaining MBPP+ 60 SHA `88a0a1e9…`; anchor SHA `fbc80466…`; complement SHA
`f03ecc3e…`. The exact lead command is in `CP40_PREP_REPORT.md` §3. The frozen split uses
+4/40 for p<0.10; +2/40 is the practical-gain floor, not a significance threshold.

## 1. Purpose and scope

The panel tests whether the header-selected pair from the 14×60 heldout matrix transfers to
a fresh 40-task HumanEval+/MBPP+ panel. It is **not** a new pair-selection experiment and
**not** a confirmatory replacement for the 14×60/12×80 evidence. The pair is frozen before
the panel; the panel measures the pair-union gain, the anchor's pass rate, the false-pass
adjustment, and the exact McNemar discordance. The panel is a **screen**: at 40 tasks the
minimum detectable effect is roughly 20 pp, so a +2/40 gain is not statistically resolvable
by itself.

## 2. Bridge split coordination

- **Split:** 20 HumanEval+ **unused** tasks + 20 MBPP+ **unused** tasks. The bridge owns the
  task IDs, the Merkle root, and the split SHA-256. The certificate must consume the
  bridge's committed split, not invent or reorder task IDs.
- **Frozen paths:** `harness/architect/queue/cp40/cp40_split.json`,
  `cp40_task_ids.json`, `cp40_task_ids.txt`, `cp40_hashes.json`, `cp40_merkle.json`.
  Panel 40 SHA-256 `14161ce8121aa9b75dafb7af443976ff0db233a88e70f22a2789b9ba53df8ffe`;
  Merkle root `bd1c8f8aaa39b6eefaca46705a2c93c5dbc23f58667c2fef4c48db0f1885bda6`;
  remaining MBPP+ 60 SHA-256 `88a0a1e913c0c9c1664804be6f5d6c93cd3c564fde2837e22e1c556c62d1f54d`.
- **Disjointness:** 0 overlap with the HumanEval heldout/dev matrices and the 12×80 fresh
  matrix; 0 overlap with the PROBE-02-V14 120-task slice; the 20 MBPP+ panel tasks are
  drawn from the 200-task draw, and the remaining 60 MBPP+ tasks stay sealed. The bridge
  records the disjointness and contamination checks; the certificate references the
  bridge's `task_list_sha256` and `merkle_root`.
- **Freshness:** the task IDs and Merkle root are committed **before** the run; the task
  text is sealed until the run; no task text is used in any training or calibration
  corpus. The panel is a scored run and requires lead approval and a bridge window.
- **Calibration split:** the false-pass certificate is calibrated on the 14×60 heldout
  matrix (eight saved configs, 18/269 false-pass) and the 12×80 fresh matrix; the panel is
  the test. The panel's own false-pass rate is a diagnostic, not the calibration source.

## 3. Arms and generations

- **Anchor:** `q3km_code_kvq8_0_preplus` (the best fixed configuration on 14×60, 36/60);
  model SHA-256 `fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb`,
  786.0 MiB, KV q8_0.
- **Complement:** `mx_q4km_code_attnq_q5k_plus` (the selected complement; the best pair
  union on 14×60 is 41/60); model SHA-256
  `f03ecc3eeb5f957f1331aae886779730bbaa9f1825d1abd075fa894407760b74`, 948.24 MiB, KV f16.
- **Generations:** 2 arms × 40 tasks = **80 generations**, one run per cell, fixed
  generation settings (6 CPU threads, ctx 2048, temp 0, top_p 1, seed 0, max 512).
- **Visible vs hidden:** visible = base HumanEval/MBPP tests; hidden = full plus tests.
  The pair union is "either arm passes." The anchor is the single anchor arm.
- **Scoring:** all plus tests, 30 s timeout, timeouts and truncations count as failures,
  request errors above 10% invalidate the run, no post-hoc task deletion.

## 4. False-pass adjustment

The panel uses the certified false-pass adjustment from `CP1_FEASIBILITY.md`:

- eight saved configs: **18/269 = 6.69%** false-pass, exact 95% CI **[4.01%, 10.37%]**;
- nine-config reference incl. F16: **21/305 = 6.89%** [4.31%, 10.33%];
- private 202-mutant set: **202/202 killed**, score lower bound **0.982**.

The panel's own visible/hidden split can estimate a panel-specific false-pass rate; report
it as a diagnostic. If the panel's false-pass rate differs from 6.69%, report both the
global-certificate CP@1 and the panel-specific diagnostic. CP@1 is **within-sample/
matrix-level**; it is not an out-of-sample guarantee and it is not conformal coverage.

## 5. CP@1 formula and interval

For task \(i\), let \(y_i\) be the visible pair-union pass (either arm passes) and
\(s_i=P(\text{hidden pass}\mid\text{visible pass})\). The certified pass@1 is

\[
\mathrm{CP@1}=\frac{1}{40}\sum_{i=1}^{40} y_i\,s_i.
\]

- **Global certificate:** \(s_i=1-\hat{f}\), \(\hat{f}=0.0669\). This is the primary
  adjustment; the nine-config 0.0689 is a sensitivity.
- **LOO variant:** if the panel has per-config visible/hidden outcomes, estimate \(s_i\)
  from the other configurations; report as a secondary. With two arms, the LOO estimate is
  the other arm's hidden/visible rate, which is noisy; label it exploratory.
- **Raw pair union:** \( \bar{y} = (1/40)\sum y_i \); the unadjusted pass rate.
- **Hidden pair union:** \( \bar{h} = (1/40)\sum h_i \); the unadjusted ground truth if the
  plus tests are scored. The CP@1 should be close to \( \bar{h} \); if it is not, the global
  false-pass adjustment is a transfer assumption and must be reported as such.
- **Interval:** report (i) the exact Clopper–Pearson interval for the raw pair union,
  (ii) the exact false-pass interval, (iii) a conservative product interval
  \([p_{\text{low}}(1-f_{\text{high}}), p_{\text{high}}(1-f_{\text{low}})]\), and (iv) a
  paired task bootstrap (10,000 resamples) for the pair-union and CP@1 differences. The
  product interval is conservative; the bootstrap is the primary interval for the paired
  gain.

## 6. Selection coverage

The panel does **not** re-select the pair; the pair is frozen before the run. The
selection-coverage field records the **source** selection certificate, not a new panel
selection:

- exact header: 14×60 selection coverage **1.000 [0.982, 1.000]**; 12×80 **1.000**;
- MinHash-512: 14×60 **1.000**; 12×80 **0.965 [0.929, 0.986]** (the 90% certificate at
  α=0.10);
- Bloom-512: 0.905/0.935 (fails); Bloom-64 fails.

The panel's **transfer coverage** is the fraction of the 40 tasks where the pair union
covers the anchor's failures, i.e. the complement's unique-pass rate. This is not the same
as the source top-1 selection coverage; label it `panel_transfer_coverage`. The 90% figure
is the source **selection coverage**, not CP@1.

## 7. Exact McNemar and decision rule

Let \(b\) = pair union passes and anchor fails; \(c\) = pair union fails and anchor passes;
\(n=b+c\). The exact one-sided McNemar p-value in the direction of the pair is

\[
p_{\text{one}} = \sum_{k=b}^{n}\binom{n}{k}0.5^{n} \quad (b>c),\qquad
p_{\text{one}}=1 \quad (b\le c).
\]

The exact two-sided p-value is
\( \min(1, 2\sum_{k=0}^{\min(b,c)}\binom{n}{k}0.5^{n}) \).
Report \(b,c\), the gain \((b-c)/40\), the exact one-sided and two-sided p-values, and a
95% paired bootstrap CI for the gain.

**Pre-registered rule (bridge §7):**

- **Success:** pair union ≥ anchor + 4/40 **and** exact one-sided McNemar p < 0.10; **or**
  the 95% CI lower bound > 0. The +2/40 request threshold is the practical-gain floor, not
  a significance threshold; a +2/40 all-win result has exact p = 0.25.
- **Failure:** pair union ≤ anchor.
- **Inconclusive:** otherwise.

**Precision note on the +2/40 threshold.** A +2/40 gain with \(b=2,c=0\) has exact
one-sided p = 0.25, so it does **not** satisfy the p < 0.10 criterion. The smallest
all-win gain that satisfies p < 0.10 is \(b=4,c=0\) (gain +4/40 = +10 pp, p = 0.0625).
A gain of +2/40 is a practical-gain floor, not a significance threshold; a +2/40 all-win
result is **inconclusive** under the pre-registered rule. The certificate must record the
full b/c grid, not only the gain. The bridge's alternative "95% CI lower > 0" is also not
met by a +2/40 all-win result under a paired task bootstrap (the 2.5th percentile is 0);
it can be met by a larger all-win gain.

## 8. Certificate template fields

The JSON template in `analysis/cp1_panel_40_certificate_template.json` has these fields:

| Field | Meaning |
|---|---|
| `certificate_id` | `CP1-PANEL-40-01` |
| `version` | `1.0` |
| `status` | `TEMPLATE` / `PENDING_RUN` / `SUCCESS` / `FAILURE` / `INCONCLUSIVE` |
| `panel` | `n_tasks` 40; `split` (20 HE+ unused + 20 MBPP+ unused; `task_ids`, `merkle_root`, `sha256`, `freshness`, `source`); `calibration_split` 14×60/12×80; `arms` (anchor/complement, SHA, size); `generations` 80 |
| `false_pass_certificate` | eight-config 18/269 = 6.69% [4.01,10.37]; nine-config 21/305 = 6.89% [4.31,10.33]; private 202/202 lower bound 0.982; panel diagnostic (optional) |
| `cp1` | formula; anchor raw union, adjusted CP@1, interval; pair raw union, adjusted CP@1, interval; hidden pair union (optional); scope |
| `selection_coverage` | source 14×60 1.000; 12×80 0.965; panel transfer coverage; note "pre-selected pair; no new top-1 selection" |
| `mcnemar` | b, c, gain_tasks, gain_rate, exact_one_sided_p, exact_two_sided_p, ci95, success_rule, failure_rule |
| `decision` | PENDING / SUCCESS / FAILURE / INCONCLUSIVE |
| `power_caveat` | 40-task screen; expected +3.3/40; MDE ~20 pp; not confirmatory |
| `provenance` | commands, environment, run_id, scored_by, lock, port, timestamp |
| `approval` | PENDING_LEAD / approved_by / window_id |
| `outcome` | PENDING / recorded_at / result_path / summary |

## 9. Analysis steps (future run; not executed)

1. Verify the bridge split: 40 task IDs, Merkle root, SHA-256, 0 overlap with HumanEval
   heldout/dev and the PROBE-02-V14 120-task slice; the 20 MBPP+ tasks are in the 200-task
   draw; the remaining 60 MBPP+ tasks stay sealed.
2. Build/verify the two arm artifacts; record SHA-256 and sizes; confirm the 2-arm budget.
3. Run 80 generations (2 arms × 40 tasks) under the fixed protocol; score visible base
   tests and hidden plus tests; record pass/fail per arm/task.
4. Compute anchor union (single arm), pair union (either arm), b/c discordance, gain,
   exact one-sided/two-sided McNemar, paired bootstrap CI.
5. Compute raw pair union, hidden pair union, global CP@1 (6.69% and 6.89%), LOO CP@1
   (secondary), and the panel-specific false-pass diagnostic.
6. Compute the source selection coverage (1.000/0.965) and the panel transfer coverage.
7. Apply the decision rule; write the certificate JSON with the observed values, CIs, and
   decision; attach the commands and SHA-256 values.
8. If the pair union ≤ anchor, the decision is FAILURE; if +2/40 or +3/40 with p ≥ 0.10,
   INCONCLUSIVE; if ≥ +4/40 all-win with p < 0.10, SUCCESS; the bridge's 95% CI alternative
   is also recorded.

## 10. Power caveat

The 14×60 expected pair gain is +5/60 = +3.3/40; a 40-task exact McNemar is a screen, not
a powered confirmation. The panel cannot resolve the 3–5 pp effects that motivated CP@1;
it is a transfer test and a public-evidence artifact. The primary evidence remains the
14×60/12×80 matrices and the 900-pair design in `VA-ROUTER-01` if a powered test is needed.

## 11. Provenance and approval

The split is frozen at `harness/architect/queue/cp40/cp40_split.json`; the exact lead
command is:

```powershell
cmd /c start "" /BELOWNORMAL /B pwsh -NoProfile -ExecutionPolicy Bypass -File "harness\architect\queue\cp40\run_cp40_lowprio.ps1"
```

The script acquires the eval lock with `python harness/team/scripts/eval_lock.py acquire
--branch architect-cp40 --port 8140 --timeout 1800`, runs the anchor and complement, then
the analysis, and releases the lock in a `finally` block. At preparation, port 8140 was
active; the launcher accepts `CP40_PORT`, so use `$env:CP40_PORT=8141` before the command
or wait until 8140 is free. Verify with `python harness/team/scripts/eval_lock.py status`.
The certificate must include the bridge split hash, the arm SHA-256 values, the run
command, the environment, and the verifier version. No model, server, lock, GPU, new
session, or commit was used to write this plan; the lead launches the run.


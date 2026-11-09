# CP@1 40-task panel — frozen split and low-priority run plan

**Status:** split **FROZEN**; **NOT RUN**. Lead authorization: V6 residual tests are
authorized as low-priority background runs. Bridge window **W26** is ready under lock
`architect-cp40`; the launcher defaults to port `8140` but accepts `CP40_PORT`. At preparation
(2026-11-09T20:22Z) the lock is **FREE** but team port **8140 is active**; the quiet check will
refuse the default, so the lead must set `CP40_PORT` to a free port or wait. The lead launches. No scored run, server, lock, GPU, new
session, or commit was used to prepare this plan.

**Certificate of record:** `harness/architect/agents/09_benchmark/CP1_PANEL_40_CERTIFICATE.md`
and `analysis/cp1_panel_40_certificate_template.json`. This plan supplies the frozen split,
IDs, Merkle root, hashes, and the run command; the 09 template remains the certificate.

## 1. Frozen panel

- **20 HumanEval+ unused** + **20 MBPP+ unused** = 40 tasks.
- Selection: one `random.Random(20261109)` stream; sample 20 from sorted `humaneval.unused`
  (64), then sample 20 from sorted `mbpp.unused` minus the PROBE-02-V14 120-task slice (80);
  sort each selection.
- **Disjointness verified:** 0 overlap with HumanEval heldout/dev; 0 overlap with the
  PROBE-02-V14 120-task slice; all 20 MBPP tasks are in the 200-task draw.
- **Remaining sealed:** 60 MBPP+ tasks from the 200-task draw; 44 HumanEval unused tasks
  remain unassigned; the 2-task reserve is untouched.

## 2. Paths and hashes

| Artifact | Path | SHA-256 |
|---|---|---|
| Frozen split | `harness/architect/queue/cp40/cp40_split.json` | `8cb2752323d6de8ddf3f013dada9771dafca02485d1a80b1c8b48c27d9d37916` |
| Task IDs (40, newline) | `harness/architect/queue/cp40/cp40_task_ids.txt` | `14161ce8121aa9b75dafb7af443976ff0db233a88e70f22a2789b9ba53df8ffe` |
| Task IDs (JSON) | `harness/architect/queue/cp40/cp40_task_ids.json` | `8f48a31dc412d0b6b8ebcdb8d90a976765e3b4fc76850c2348a43aaeccbcf0be` |
| Hash bundle | `harness/architect/queue/cp40/cp40_hashes.json` | `7c9f0d5fabb1936b3e7aaf44de0f162acba88ad26eaeace51b1b8e33a97e4007` |
| Merkle leaves/root | `harness/architect/queue/cp40/cp40_merkle.json` | `a3d68d5f3d2f7a50f083d0ad9cbfd9817a0ccbca1ffd457e6d2582668008c09e` |
| Freeze script | `harness/architect/queue/cp40/freeze_cp40.py` | `423610ccda762f82bda998cc9821bf2a3652484d9662e925601048f2ff3f1021` |
| Run wrapper | `harness/architect/queue/cp40/run_cp40.py` | `046676b8dd14a3f18d0038c60aeea7dd02806b830f14c151045f0eb0f82ec726` |
| Analysis | `harness/architect/queue/cp40/cp40_analysis.py` | `5f61d48e31866b1779b8280e120ddd91d099425011647fae80d83ae915b7e65b` |
| Low-priority launcher | `harness/architect/queue/cp40/run_cp40_lowprio.ps1` | `10725f50bcda4d2db84b20675bef1e66ca28dd0616eee460bf3f83dcef231685` |

**Canonical panel hashes:** 40-task newline `14161ce8…8ffe`; JSON `85bc108b…5c88`;
HumanEval 20 `e003541f…88e4`; MBPP 20 `305629b9…4896`.
**Merkle root:** `bd1c8f8aaa39b6eefaca46705a2c93c5dbc23f58667c2fef4c48db0f1885bda6`
(SHA-256 leaves over `dataset/split/task_id`, duplicate last leaf on odd count).
**Remaining 60 MBPP+ sealed:** `88a0a1e913c0c9c1664804be6f5d6c93cd3c564fde2837e22e1c556c62d1f54d`.
**Parents:** `splits.json` `dd5cd10676843ac3e8ebf2a7ed7190db0421aa3ee1c821ea4009824e8624d12d`;
200-task draw `657da3bcc98e41ca35bd7bca6478bc3702aa4a30a6461bb78d055d14cec16d27`;
PROBE-02-V14 slice `6cc354f4bcb2d7d8b549e250e9b1e01a4066ef14b61f31a76a82d82e6bb628cf`.

## 3. Arms and model SHAs

| Role | Config | Model | SHA-256 | Size | KV |
|---|---|---|---|---:|---|
| Anchor | `q3km_code_kvq8_0_preplus` | `harness/models/Qwen2.5-Coder-1.5B-Instruct/quants/q3km_code.gguf` | `fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb` | 786.00 MiB | q8_0 |
| Complement | `mx_q4km_code_attnq_q5k_plus` | `.kilo/worktrees/team-mixed-precision-11b2d5e6a01a29c5/harness/mixed/quants/mx_q4km_code_attnq_q5k.gguf` | `f03ecc3eeb5f957f1331aae886779730bbaa9f1825d1abd075fa894407760b74` | 948.24 MiB | f16 |

2 arms × 40 tasks = **80 generations**; one run per cell; 6 CPU threads, ctx 2048,
temperature 0, top_p 1, seed 0, max 512, batch/ubatch 512; plus tests, 30 s timeout;
timeouts/truncations count as failures; request errors >10% invalidate; no post-hoc deletion.

## 4. Decision rule (precision-corrected)

- **Success:** combined pair union − anchor **≥ +4/40** and exact one-sided McNemar
  **p < 0.10**, or the **95% paired-bootstrap CI lower bound > 0**.
- **Failure:** combined pair union **≤ anchor**.
- **Inconclusive:** otherwise, including +2/40 and +3/40.
- **Precision:** +2/40 all-win has exact one-sided p=0.25; +3/40 p=0.125; +4/40 p=0.0625.
  +2/40 and +3/40 are a practical-gain floor, **not** significance; +2/40 all-win is
  inconclusive. Report b/c, gain, one-sided and two-sided p, and the paired bootstrap CI.
- HumanEval 20 and MBPP 20 are reported separately as descriptive subgroups, not
  decision-bearing.
- The panel is a **transfer screen**, not a second confirmation; the 14×60/12×80 matrices
  remain the primary evidence.

## 5. CP@1 certificate fields

Use the 09 certificate template. Key fields to populate from the run:

- **False-pass adjustment:** 18/269 = **6.69%** [4.01%, 10.37%] (eight configs);
  21/305 = **6.89%** [4.31%, 10.33%] (nine-config); private 202/202, lower bound **0.982**.
- **CP@1:** `(1/40) Σ y_i s_i`; global adjustment 0.0669; nine-config sensitivity 0.0689.
  Report raw pair union, adjusted CP@1, hidden pair union, exact Clopper–Pearson interval,
  conservative product interval, and paired task bootstrap (10,000 resamples).
- **Source selection coverage:** 14×60 **1.000** [0.982, 1.000]; 12×80 **0.965**
  [0.929, 0.986]. The panel is a pre-selected-pair transfer test; report
  `panel_transfer_coverage` separately.
- **Scope:** within-sample/matrix-level; not an out-of-sample guarantee; not conformal.

## 6. Exact command the lead launches (low priority)

```
$env:CP40_PORT=8141; cmd /c start "" /BELOWNORMAL /B pwsh -NoProfile -ExecutionPolicy Bypass -File "harness\architect\queue\cp40\run_cp40_lowprio.ps1"
```

At preparation, 8140 was reported active and 8141 was not. Verify with
`python harness/team/scripts/eval_lock.py status`; if 8140 is free, omit the `$env:CP40_PORT` assignment and the
launcher defaults to 8140. Do not use a port the status reports active.

The launcher sets itself and the server processes to **BelowNormal**, acquires the eval lock
with branch `architect-cp40` on the selected `CP40_PORT` (default `8140`), runs the anchor (q8_0 KV), the complement (f16
KV), then `cp40_analysis.py`, and releases the lock in `finally`. It does not start any run
until the lead executes the command.

## 7. No-run status and missing item

- The split is frozen; the run command is ready; **the bridge has not launched it**.
- Missing before launch: none for the split. The lead must launch the command and record the
  run ID/approval; the certificate template remains `TEMPLATE` until the run completes.
- The 09 certificate is the record of decision; `cp40_analysis.json` supplies the
  McNemar/decision fields, and the certificate fields above are filled from the run.

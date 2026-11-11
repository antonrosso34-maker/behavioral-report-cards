# Gemma E2B two-family audit — aggregate evidence

This folder contains the aggregate evidence for the Gemma E2B two-family audit in the final paper
`paper/FINAL_PAPER_DRAFT_V1.md`. It contains **pass matrices, task IDs, sanitized summaries, and
aggregate statistics only**; it does not contain raw model completions, model weights, or private data.

## Scope

The audit compares five Gemma E2B configurations (`q3_mix`, `gp1_qat_requant`,
`google_qat_q4_0`, `udq4_k_xl`, `udq2_k_xl`) against Unsloth UD-Q4_K_XL (2,498.98 MiB) on
HumanEval dev 40, HumanEval heldout 60, and MBPP heldout 60. The sealed MBPP panel is used for the
development result; the HumanEval pair is the public portfolio claim.

## Key aggregate results

- **HumanEval pair `q3_mix + gp1`:** 42/60 vs 36/60; b=7, c=1; exact one-sided **p=0.0352**;
  two-sided 0.0703; partial credit **+9.01 pp**, task-clustered 95% CI [+1.36, +17.27],
  sign-flip p=0.027, cluster-robust p=0.021. Size 5,432.83 MiB (2.17× Unsloth).
- **Sealed MBPP pair:** 40/60 vs 40/60; b=4, c=4; exact one-sided p=0.6367; a real tie.
- **Old MBPP pair:** 34/60 vs 35/60; b=4, c=5; exact one-sided p=0.7461; two-sided 1.0000;
  a loss. (The value 0.5000 is the opposite tail, not the stated team endpoint.)
- **Repair@1 development result:** sealed 44/60 vs 40/60, b=4, c=0, p=0.0625, post-hoc;
  old 38/60 vs 35/60, b=4, c=1, p=0.1875. Full sweep: team pair +4/+4; Unsloth 0/45;
  Google 0/45; 184/197 unmatched. Fresh 68-task panel needs k≥4 repair-only tasks and 0
  Unsloth repairs; under the Qwen-proxy rate (3/118 = 2.54%), P(≥4)=9.5%. High-risk
  confirmation, not a predicted win.
- **PC-McNemar:** HE heldout +9.01 pp (p=0.027), dev +8.09 pp (p=0.098), sealed MBPP
  +5.50 pp (p=0.185), old MBPP −1.88 pp (p=0.673). Task-family-specific: HE robust,
  MBPP partial-credit dead.
- **Size-matched `gp1b_2498`:** 2,492.99 MiB; dev 34/40 vs 29/40, b=7, c=2, p=0.0898;
  heldout 34/60 vs 36/60, b=3, c=5, exact one-sided p=0.8555, two-sided 0.7266; MBPP partial
  17/32 vs 20/32. A dev win + heldout near-tie, not a heldout win. (The value 0.3633 is the
  opposite tail, not the stated team endpoint.)
- **Cross-family secondary:** `gp1_2629 + q5ks_none` 45/60 vs 36/60; b=10, c=1;
  p=0.0059; 1.476×; Gemma arm 34/60, Qwen arm 33/60; 11+12 unique tasks; both arms
  individually lose to Unsloth; HumanEval-only, no MBPP measurement.
- **Failure correlation:** four-arm Spearman(pass correlation, C) = −0.8095; partial
  −0.3404; the team-only q3+gp1 MBPP pair is the wrong complement.

## p-value convention

The exact McNemar endpoint is the one-sided team-superiority probability
`P(Bin(b+c, 0.5) >= b)`; the two-sided value is `2 * min(P(>= b), P(<= b))`. The old-MBPP
row (b=4, c=5) is one-sided 0.7461 / two-sided 1.0000; the gp1b heldout row (b=3, c=5) is
one-sided 0.8555 / two-sided 0.7266. The values 0.5000 and 0.3633 are the opposite tails and
are not the stated endpoint. The conclusions are unchanged: the old MBPP is a loss; the
gp1b heldout is a near-tie.

## Freshness disclosure

The 64 HumanEval and 76 MBPP `stage2_cal` tasks were scored by four Qwen2.5-Coder-1.5B
configs on 2026-11-08. The Fresh-132 is **campaign-fresh** (not used by any Gemma arm), not
unseen by the project. Under a strict never-scored definition, the fresh pool is 2 MBPP + 0 HE.

## Files

- `sealed60_analysis.json` / `.md` — aggregate sealed-60 pair/union analysis.
- `pass_matrix_{sealed60,old60,he_dev40,he_heldout60}.csv` — task × arm pass bits (1/0).
- `task_ids_*.txt` — the task IDs for each matrix.
- `summaries/` — sanitized per-arm summaries (size, SHA-256, pass count); no local paths.
- `repair_summary.json` — repair@1 development result and fresh fragility.
- `pc_mcnemar_summary.json` — four-split partial-credit analysis.
- `fresh132_summary.json` — Fresh-132 counts, power, freshness.
- `cross_family_summary.json` — cross-family pair.
- `SHA256SUMS` — hashes of the files in this folder.

## License

The public release is CC BY 4.0 for the evidence/paper and MIT for the code; the model
weights are Apache-2.0. The raw completions and model weights are not included.

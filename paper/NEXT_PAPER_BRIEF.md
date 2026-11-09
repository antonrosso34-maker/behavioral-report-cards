# Next paper brief: report cards or Q-Adapter repair?

**Date:** 2026-11-09.
**Status:** writing/design only. No scored run, server, lock, GPU, new session, or commit.
**Recommendation:** **Option A — Behavioral Report Cards / deployment audit standard.**

## Option A: Behavioral Report Cards / deployment audit standard

**Positive claim.** An 8/10-byte exact pass-set header is a deployment audit artifact for a fixed evaluation matrix: pass rates, unique tasks, pair/union complementarity, regression flags, and certificate checks are exact and cheap. The header is not a selector; split-half and cross-matrix transfer are explicitly out of scope and reported as the boundary.

**Evidence.**

- Exact headers: 8 B/60 tasks, 10 B/80; lossless; best pairs 41/60 and 56/80; best fixed 36/60 and 49/80; oracle 43/60 and 58/80.
- Report-card demo (`harness/architect/queue/report-card-demo/`): best pair `q3km_code_kvq8_0_preplus + mx_q4km_code_attnq_q5k_plus` at 41/60; complement passes 31/60 alone but only 5 of its 31 passes are outside the baseline, so the pair gain is 5, not 31; a standalone ranking misses the best deployment pair.
- Gemma second family (`harness/architect/agents/04_routing/GEMMA_SECOND_FAMILY.md`): 5 B/40 and 8 B/60 headers; within-sample 0.00/0.00/1.00 and CP@1 1.000; the storage boundary replicates exactly, while transfer replicates qualitatively (target-best pair selected 0/6 directions; regret 1–6 tasks; heldout→MBPP 37/60 vs 38/60; MBPP→heldout 37/60 vs 43/60).
- Certificate layer: probe passport, claim.cert, Rule CI, CP@1, Rule certificates EXACT-HEADER-PAIR-01/CROSS-01. Exact-header CP@1 0.6376/0.6532; selection coverage 1.000 [0.982, 1.000]; false-pass 18/269 = 6.69%, 21/305 = 6.89%, private 202/202 killed, LB 0.982.
- Public manifest: `harness/architect/queue/evidence/pass-set-header/`; 17 files + `SHA256SUMS`; 7 claims, no orphans; zip SHA-256 `de9951744236499cfdea62efae129b65465c004c9f7e61593c23719edbb948e9`; GitHub commit `be038a5bffdceb51af6e4aa09779aee7ec5c6cd3`; DOI/release pending.

**Minimal remaining work.**

1. 40-task CP@1 panel and an independent OOS/cross-matrix confirmation.
2. One external selector baseline beyond Bloom-512, Bloom-64, and random projection.
3. Public release/DOI.
4. Keep the claim scoped: exact storage and audit for the observed matrix, not selection transfer.

**Risk.** Reviewers may call it an engineering/reporting paper rather than a method paper. The 40-task panel is the main missing evidence; the negative transfer boundary must be framed as the contribution.

## Option B: Q-Adapter post-quantization flip-margin repair

**Claim.** A small adapter trained to restore decision margins after quantization reduces flips and improves pass-set coverage without retraining the base model.

**Evidence needed.**

- Per-decision margins for the existing 14×60/12×80 matrices (Wu et al. 2026 preprint margin law).
- A Q-Adapter (LoRA rank 8–16 on attention/MLP) trained on margin restoration; compare no-adapter, adapter, and full precision.
- Paired held-out pass/fail, flip rate, margin recovery, and cost; cross-family check.
- A pre-registered gate: the adapter must improve pass-set coverage or reduce flips by a meaningful margin without regressions.

**Training/build cost.** 1–2 GPU-days per model/config for adapter training, plus calibration and evaluation; new builds and a training harness. This is outside the current no-GPU constraint.

**Risk.** High. Margin repair may improve margins without pass-set gains; the adapter may not transfer across quantizers; deployment complexity increases. V6's negative transfer boundary suggests selection is hard, but adapter repair is a different intervention; the probability of a positive result is unknown.

## Recommendation

Choose **Option A**. It has a positive, scoped claim that survives V6's negative transfer boundary, strong existing evidence (exact headers, report-card demo, Gemma storage replication, certificate layer, public manifest), and minimal remaining work (public release plus the 40-task confirmation). Option B requires new training/build and has a higher risk of a null result; it should be a follow-on only if the team wants a method paper and can fund the GPU work.

**Decision rule.** If the 40-task CP@1 panel and public release land, submit Option A. If Option B's margin-repair pilot shows a pre-registered pass-set gain, revisit it as a separate paper; do not merge the two claims.

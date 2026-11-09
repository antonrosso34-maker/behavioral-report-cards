# Next paper input: Behavioral Report Cards for Quantized Code Models

**Status:** outline/design input. No scored run, server, lock, GPU, new session, or commit. The paper uses existing evidence only; the transfer boundary is reported as a limitation, not a hidden failure.

## Title

**Behavioral Report Cards for Quantized Code Models: Exact Pass-Set Headers and Deployment Audits**

## Positive claim

For a fixed evaluation matrix, an **8/10-byte exact pass-set header** makes deployment audits and pair/union analysis exact and cheap, and a certificate layer makes the audit boundary explicit. On Qwen 14×60 and 12×80, the exact header selects the true best pair (**41/60** and **56/80**), and the report card shows that a complement passing **31/60** alone contributes only **5** unique tasks outside the baseline—so the pair gain is **5, not 31**. On Gemma, the storage boundary replicates exactly (**5 B/40**, **8 B/60**; 0.00/0.00/1.00), while transfer remains qualitative. The header is a report card, not a selector.

## Evidence table

| Evidence | Qwen 14×60 | Qwen 12×80 | Gemma | V6 residual |
|---|---|---|---|---|
| Header size | 8 B | 10 B | 5 B/40; 8 B/60 | 13×80 KV8-inclusive |
| Within-sample regret / MAE / top-3 | 0.00 / 0.0000 / 1.00 | 0.00 / 0.0000 / 1.00 | 0.00 / 0.00 / 1.00 | — |
| Best pair union | 41/60 | 56/80 | exact by construction | KV8 adds 0 union |
| Selection coverage | 1.000 [0.982, 1.000] | 1.000 [0.982, 1.000] | 1.000 within-sample | — |
| CP@1 (certified pass@1) | 0.6376 | 0.6532 | 1.000 | CP40: 0.4199/0.4190 |
| False-pass certificate | 18/269 = 6.69% [4.01, 10.37]; 21/305 = 6.89% [4.31, 10.33]; private 202/202 killed; LB 0.982 | same certificate | — | — |
| Split-half | 1.91 regret; 3.00 [1.15, 7.40] MAE; 0.208 [0, 1] top-3 | 1.70; 3.47 [1.00, 8.97]; 0.079 [0, 1] | MAE 2.12/3.02/2.98; CP@1 0.176/0.000/0.000 | — |
| Cross-matrix | 48/80 vs 56/80; regret 8.0; top-3 0.0 | 34/60 vs 39/60 common-config; regret 5.0; top-3 0.0 | 0/6 target-best directions; regret 1–6; heldout→MBPP 37/60 vs 38/60; MBPP→heldout 37/60 vs 43/60 | 13×80: regret 7; top-3 0; boundary unchanged |
| 40-task panel (CP40) | — | — | — | anchor 17/40; complement 15/40; union 18/40 (+1); exact one-sided p=0.5; paired CI [0,3]; HE +1 (p=0.5); MBPP 0 gain (FAILURE); 1 anchor timeout |
| Report card | best pair 41/60; complement 31/60; 5 unique outside baseline; pair gain 5, not 31 | — | — | — |

**External selector baseline.** Within-sample, the exact header is unbeatable. Out-of-sample, MinHash-512 (2,048 B) beats it on the 12×80 split-half on all four metrics: **1.45 regret / 3.26 MAE / 0.150 top-3 / 0.120 CP@1** vs **1.70 / 3.45 / 0.080 / 0.047** (selector-baseline recomputation; the main split-half table reports the Rule CI values 3.47/0.079). Random projection at 8/10 B beats it on 12×80→14×60 regret/MAE (**4 vs 5; 0.0323 vs 0.0630**) but not top-3/CP@1. The learned L1 selector is worse everywhere. Cross-matrix, no selector transfers: all top-3/CP@1 **0/0**. The audit paper's claim is exact storage/audit for the fixed matrix, not the best out-of-sample selector.

**Manifest.** `harness/architect/queue/evidence/pass-set-header/`; 17 files + `SHA256SUMS`; 7 claims, no orphans; exact headers lossless; MinHash 2,048 B (64-byte claim retracted); zip SHA-256 `de9951744236499cfdea62efae129b65465c004c9f7e61593c23719edbb948e9`; GitHub commit `be038a5bffdceb51af6e4aa09779aee7ec5c6cd3`; DOI/release pending. Report-card demo: `harness/architect/queue/report-card-demo/`.

## Section outline

1. **Introduction.** Deployment is judged by which tasks a configuration passes; fixed-matrix audits need exact, cheap pass-set storage. The header is a report card, not a selector. Contributions: exact 8/10-byte headers, exact audit/pair-union analysis, certificate layer, Qwen + Gemma evidence, and the transfer boundary.
2. **Related work.** PTQ methods (GPTQ, AWQ, SpQR), mixed-precision allocation (AMQ), sketches (MinHash, Bloom), compression evaluation (CompressionBench, LLM-KICK, ACBench). Position: storage/audit, not a new quantizer.
3. **Method.** Behavioral pass sets; exact bitset (60 tasks = 8 B; 80 tasks = 10 B); report card (pass rate, unique tasks, all pairwise unions, regression flags, best partners); certificate layer (probe passport, claim.cert, Rule CI, CP@1, Rule certificates EXACT-HEADER-PAIR-01/CROSS-01).
4. **Evidence.** Qwen 14×60/12×80 table; report-card 5-not-31 insight; Gemma second family (storage exact, transfer qualitative); V6 residual results (KV8-inclusive 13×80 cross-matrix negative; CP40 40-task panel inconclusive on HE and failing on MBPP); public manifest and reproducer.
5. **Limitations: the negative transfer boundary.** Split-half and cross-matrix selection do not transfer: 1.91/1.70 regret, 3.00/3.47 MAE, 0.208/0.079 top-3; 48/80 vs 56/80 and 34/60 vs 39/60 common-config; target oracle never in source top-3; KV8 absent from 12×80. KV8-inclusive 13×80: negative; KV8 adds 0 union; regret 7; top-3 0; boundary unchanged. CP40 40-task panel: anchor 17/40, complement 15/40, union 18/40 (+1), exact one-sided p=0.5, paired CI [0,3], INCONCLUSIVE; HE +1 (p=0.5); MBPP 0 gain (FAILURE); CP@1 0.4199/0.4190; one anchor timeout. External selector baseline: within-sample exact is unbeatable; out-of-sample MinHash-512 beats it on all four 12×80 split-half metrics (1.45/3.26/0.150/0.120 vs 1.70/3.45/0.080/0.047), random projection beats it on 12×80→14×60 regret/MAE (4 vs 5; 0.0323 vs 0.0630), the learned L1 selector is worse, and no selector transfers cross-matrix (top-3/CP@1 0/0). Gemma transfer is qualitative (0/6 target-best; regret 1–6). The header is set-level only; task routing is at chance (LOTO AUC 0.5612). CP@1 is within-sample, not conformal, not out-of-sample. The audit paper does not claim transfer or best out-of-sample selection; the boundary is a limitation. V6 can be finalized with the negative boundary.
6. **Minimal remaining work.** DOI/release only. The 40-task CP@1 panel, KV8-common cross-matrix, and external selector baseline are completed; V6 can be finalized with the negative boundary.
7. **Claims not made.** No selector; no out-of-sample/cross-matrix selection; no claim to be the best out-of-sample selector (MinHash-512 and random projection can beat the exact header out-of-sample); no new quantizer, SOTA, or all-around win; no per-task router; no conformal guarantee; no claim that 8 B vs 10 B is an ablation; no claim that the 60/80-task matrices are a full benchmark; no claim that the 40-task panel establishes transfer (it is inconclusive on HE and fails on MBPP).
8. **Artifacts.** Manifest, report-card demo, Rule certificates, CP@1 certificate (`harness/architect/agents/09_benchmark/EXACT_HEADER_CP1.md`), Gemma evidence (`harness/architect/agents/04_routing/GEMMA_SECOND_FAMILY.md`), public commit.

## What makes the paper positive

The positive result is exact storage and audit, not selection transfer or best out-of-sample selection. The paper says: for a fixed matrix, the pass set is small enough to store exactly; audits, pair/union queries, and regression flags are exact and cheap; the certificate layer tells the reader exactly what the header can and cannot claim. The 5-not-31 report-card insight is the practical demonstration: standalone ranking would discard the best deployment pair.

## Claims not made

- No claim that the header selects a configuration on a new matrix.
- No claim that the exact header is out-of-sample or cross-matrix exact.
- No claim that Gemma transfer replicates numerically; storage replicates exactly, transfer qualitatively.
- No claim that the 60/80-task matrices are a full code benchmark; the 40-task panel is inconclusive on HE and fails on MBPP.
- No claim that CP@1 is conformal or an out-of-sample guarantee.
- No claim that the 8 B vs 10 B sizes are an ablation; they are per-matrix sizes.
- No claim that the report card replaces full evaluation; it is a descriptive audit of an existing pass set.

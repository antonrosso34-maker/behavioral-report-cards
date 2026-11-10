# Behavioral Report Cards, Not Selectors: Exact Pass-Set Headers and the Transfer Boundary

**Status:** V12 draft for red-team. The report card is exact for the observed pass set; the transfer boundary is negative; no model-quality/SOTA claim. Analysis/design; no scored run in this draft.

## Abstract

For a fixed evaluation matrix, quantization configuration selection is usually driven by weight error or perplexity, but deployment is judged by which tasks a configuration passes. The pass set is small enough to store exactly: 60 tasks in 8 bytes, 80 in 10. We turn it into a behavioral report card: within the observed matrix, pair and union queries are exact (0.00 regret, 0.0000 MAE, 1.00 top-3; CP@1 0.6376 (14×60) / 0.6532 (12×80), point; the 0.612/0.627 values are upper-false-pass sensitivity, not a joint interval; selection coverage 1.000 by construction (the 200-seed interval is for sketch comparators); raw union 0.683/0.700). The best pairs are 41/60 and 56/80; the report card shows a complement passing 31/60 alone contributes only 5 unique tasks, so the pair gain is 5, not 31.

The exactness does not transfer: split-half 1.91/1.70 regret, 3.00/3.47 MAE, 0.208/0.079 top-3; cross-matrix 48/80 vs 56/80 and 34/60 vs 39/60 common-config; KV8-inclusive 13×80 adds 0 union; the CP40 panel is inconclusive (union 18/40 vs 17/40, p=0.5; MBPP subgroup failure); Gemma storage replicates exactly but transfer does not. External sketches can beat the exact header on some out-of-sample metrics, but no selector transfers the target-best. The report card is the contribution; the exact header is not a selector. The claim is exact storage/audit for the observed matrix and an auditable transfer boundary, not near-oracle out-of-sample selection.

## 1. Introduction

The prior V2 study found a split negative result: risk3 improved code-tail NLL over q4km_none and WikiText over q4km_code, but no in-house point was significantly better on both axes against the same public baseline; the evidence was local-only; and the code evaluation was a 10-task screen. Those negative results expose the missing primitive: a compact, auditable way to store the pass set without re-running every configuration.

This paper supplies that primitive and reports its boundary. A behavioral pass set is the set of probes a configuration passes. The exact representation is a bitset: 60 tasks in 8 bytes, 80 in 10. Because the bitset is the pass set, pair and union selection is exact **within the observed pass set**. The exactness does not survive a 50/50 split-half, a cross-matrix transfer, or a KV8-inclusive matrix; the fresh 40-task panel is inconclusive; the Gemma second family replicates the storage boundary while transfer fails (does not replicate numerically).

**Contributions.**

1. **Behavioral report card.** The exact pass-set bitset (8 B/60, 10 B/80) is one bit per task; it answers all 91 pair/union queries for the 14×60 matrix without re-running the 14 configurations (840 generations); the 31/60 complement contributes 5 unique tasks, not 31. **The bitset/union is standard; the contribution is the empirical complementarity and the observed failure of selection to transfer, packaged as an audit artifact and certificates.**
2. **Within-sample exactness.** 0.00 regret, 0.0000 MAE, 1.00 top-3; selection coverage 1.000; CP@1 0.6376/0.6532; raw union 0.683/0.700; false-pass 18/269, 21/305, private 202/202, LB 0.982; best pair 41/60, 56/80; set-level only (LOTO AUC 0.5612).
3. **Boundary.** Split-half 1.91/1.70 regret, 3.00/3.47 MAE, 0.208/0.079 top-3 (40.5%/41.1% config stability); cross-matrix 48/80 vs 56/80 and 34/60 vs 39/60 common-config; KV8 13×80 adds 0 union; CP40 +1/40, one-sided p=0.5, INCONCLUSIVE, MBPP failure, CP@1 0.4199 global/0.4190 nine-config; Gemma storage exact but transfer fails.
4. **External-selector nuance.** Within-sample exact header unbeatable; out-of-sample MinHash-512/random projection can beat it on some metrics; L1 worse; no selector transfers the target-best.
5. **Certificate and staged evidence.** Probe passport, claim certificates (`CERTIFICATES.json`), Rule CI, CP@1, Rule certificates; staged manifest/bundle 17/17 and 79/79; public release (GitHub `behavioral-report-cards`) and the Hugging Face model (`AntonROSSO/qwen2.5-coder-1.5b-mx2-aq6-q3ks`) live; DOI pending.

## 2. Related work

GPTQ/AWQ/SpQR/llama.cpp k-quants, AMQ, CompressionBench, LLM-KICK, and ACBench show that weight error and perplexity can miss capability; MinHash/Bloom are standard set sketches. Yang et al. (2024) propose report cards as natural-language summaries of model behavior, evaluated by specificity, faithfulness, and interpretability; their unit is the qualitative summary, ours is the exact per-task pass set of a configuration, with pair/union analysis and a transfer-boundary certificate. Li et al. (2024) evaluate quantized LLMs at the aggregate level across 11 model families and five task types; they guide method selection by average performance and do not report per-configuration pass-set complementarity or the split-half/cross-matrix transfer boundary that our certificate makes explicit. The distinction is the evidence unit (exact pass set vs natural-language summary) and the certificate (transfer boundary vs aggregate recommendation). The exact header is a storage/evidence contribution, not a quantizer or a selection claim.

## 3. Method

### 3.1 Behavioral pass sets and exact bitset

For each configuration \(c\), the pass set \(P_c\) is the set of probes it passes under a fixed protocol. The probe passport records task ID, prompt hash, seed, runtime, result, and timestamp, so \(P_c\) is reproducible without the transcript.

The exact representation is a bitset: **60 tasks = 8 bytes** (4 padding bits), **80 tasks = 10 bytes**. The 8/10-byte headers are per-matrix sizes, not an ablation, and are not derived from MinHash. The exact header is 256×/204.8× smaller than MinHash-512 and 8×/6.4× smaller than Bloom-512.

### 3.2 Secondary sketch and comparators

**MinHash-512** stores 512 31-bit minima at 4 bytes each = **2,048 B** (4,096 B as int64); the earlier 64-byte claim is retracted. It meets the regret+MAE bars in **100%/96.5%** of within-sample cases; top-3 **1.00/0.99**; selection coverage **1.000/0.965**; CP@1 **0.6376 [0.491, 0.764]/0.6526 [0.524, 0.763]**; all-four unestimated. Its union MAE is 0.0079/0.0056, not zero.

**Bloom-512** uses 64 B (8×/6.4× the exact header): 0.245/0.13 regret, 0.0222/0.0306 MAE, 0.95/0.94 top-3, meeting the regret+MAE bars in 71%/47%; selection coverage 0.905/0.935; CP@1 0.6338/0.6517 (below exact). **Bloom-64** and **random projection** at 8/10 B fail on regret/MAE; CP@1 not estimated for them.

### 3.3 Selection, split-half, cross-matrix, and KV8

**Within-sample.** The bitset is the pass set, so the oracle pair/union is available without prediction: 0.00 regret, 0.0000 MAE, 1.00 top-3.

**Split-half.** A 50/50 task split selects on one half and evaluates on the other. The exact header does not make the rule out-of-sample exact; Rule certificate **EXACT-HEADER-PAIR-01** records the gap (\(\alpha = 0.05\), seed 20261109, \(B = 2000\), SHA-256 407f9587c57c99d7a68b90fc741b0ac11559817ce0642df19bc03f4fbbcd8273).

**Config stability.** The full-matrix best pair is the top pair in only 40.5%/41.1% of configuration resamples; best-pair union is 39.72 [37, 41]/54.84 [52, 56]. This is config-set stability, not split-half.

**Cross-matrix.** The full 14×60 best pair is not evaluable on 12×80 because KV8 is absent; the table uses 12 common configs. Rule certificate **EXACT-HEADER-CROSS-01** records the failure (\(\alpha = 0.05\), seed 20261109, \(B = 2000\), SHA-256 6c045220bf7b4a73cafd363ecbdec8b046255bab0e5ebfa5c7ae6a86b551f320). The KV8-inclusive 13×80 matrix adds 0 union and leaves the boundary unchanged.

### 3.4 Certificate layer

- **Probe passport.** Per-probe identity and execution record.
- **claim.cert.** Claim text, scope, estimand, point estimate, 95% CI, sign convention, evidence pointers, verifier, expiry.
- **Rule CI.** Bootstrap CI over tasks and configurations for the selection rule.
- **CP@1.** Certified pass@1 point estimate: the false-pass-adjusted value \(\mathrm{CP@1}=(1/N)\sum_i y_i s_i\) (0.9331 multiplier), with 0.612/0.627 as upper-false-pass sensitivity (0.8963 multiplier) and the global certificate. It is within-sample/matrix-level, not conformal, not out-of-sample. Selection coverage (top-1 pair = true best) is 1.000 by construction (the 200-seed interval is for sketch comparators), separate from CP@1. **In this paper every table labels the two separately; selection coverage is never called CP@1, including the external-selector tables.**
- **Rule certificates.** EXACT-HEADER-PAIR-01 and EXACT-HEADER-CROSS-01 bind the exactness and the split-half/cross-matrix boundaries.

### 3.5 Use case: behavioral report card

For a fixed evaluation matrix, the header is a behavioral report card: the 8/10-byte bitset is the pass set, so audits and pair/union queries are exact and cheap. On the 14×60 matrix, the best pair is `q3km_code_kvq8_0_preplus + mx_q4km_code_attnq_q5k_plus` at 41/60; the complement passes 31/60 alone but only 5 of its passes are outside the baseline, so the pair gain is **5, not 31**; a standalone rank overstates it by 26 tasks. The report card answers all 91 pairwise queries from the stored 8-byte headers without re-running the 14 configurations (840 generations); the local runtime is a local observation (~1 s; no timing artifact is released) (`report_card.py`). The header is not a selector; for a new matrix, the certificate says selection is not transferable. A proposed next test (not evidence) is a repository/agentic benchmark (REPO-COMP-40: 40 repo tasks, 20 discovery + 20 confirmation, 2 configs, 80 agent runs; 3 B discovery / 5 B full header; pair gain ≥2; public-test false-accept ≤0.10).

### 3.6 Second family

Gemma E2B (5 configs: q3_mix, google_qat_q4_0, gp1_qat_requant, udq4_k_xl, udq2_k_xl; splits he_dev 40, he_heldout 60, MBPP 60) gives exact headers 5 B/40 and 8 B/60; within-sample 0.00/0.00/1.00; split-half MAE 2.12/3.02/2.98; cross-matrix target-best 0/6, regret 1–6. Storage replicates exactly; transfer does not replicate numerically (failure).

## 4. Results

### 4.1 Within-sample evidence table

| Representation | Size/config | Tasks | Pair regret | Union MAE | Top-3 | Best pair union | Selection coverage [95% CI] | CP@1 | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| **Exact bitset (14×60)** | **8 B** | 60 | **0.00** | **0.0000** | **1.00** | **41/60** | 1.000 by construction | **0.6376** | verifies 0.05/0.10 |
| **Exact bitset (12×80)** | **10 B** | 80 | **0.00** | **0.0000** | **1.00** | **56/80** | 1.000 by construction | **0.6532** | verifies 0.05/0.10 |
| MinHash-512 (14×60) | 2,048 B | 60 | 0.00 | 0.0079 | 1.00 | 41.0 mean | 1.000 [0.982, 1.000] | 0.6376 | regret+MAE 100% |
| MinHash-512 (12×80) | 2,048 B | 80 | 0.045 | 0.0056 | 0.99 | 55.955 mean | 0.965 [0.929, 0.986] | 0.6526 | regret+MAE 96.5% |
| Bloom-512 (14×60) | 512 bits | 60 | 0.245 | 0.0222 | 0.95 | — | 0.905 [0.856, 0.942] | 0.6338 | regret+MAE 71% |
| Bloom-512 (12×80) | 512 bits | 80 | 0.13 | 0.0306 | 0.94 | — | 0.935 [0.891, 0.965] | 0.6517 | regret+MAE 47% |
| Bloom-64 | 64 bits | 60/80 | fails | fails | fails | — | — | fails | fails |
| Random projection (14×60) | 8 B | 60 | 4.00 | 0.0555 | fails | — | — | fails | fails |
| Random projection (12×80) | 10 B | 80 | 2.00 | 0.0452 | fails | — | — | fails | fails |

**Notes.** Exact rows are constructions; 8 B/10 B are per-matrix sizes; the exact header selects the true best pair (41/60, 56/80). Set-level only (LOTO AUC 0.5612). CP@1 is a point estimate (0.612/0.627 upper-false-pass sensitivity); selection coverage separate; 40.5%/41.1% config stability.

### 4.2 Split-half and config stability

| Matrix | Regret [95% CI] | Union MAE [95% CI] | MAE rate | Top-3 [95% CI] |
|---|---:|---:|---:|---:|
| **14×60** | **1.91 [0, 6]** | **3.00 [1.15, 7.40]** | **0.100** | **0.208 [0, 1]** |
| **12×80** | **1.70 [0, 4]** | **3.47 [1.00, 8.97]** | **0.087** | **0.079 [0, 1]** |

Config stability: best-pair union 39.72 [37, 41]/54.84 [52, 56]; top-pair frequency 40.5%/41.1%. This is not split-half. The out-of-sample bars are not met.

### 4.3 Cross-matrix and KV8

| Direction | Selected pair | Selected union | Best-pair oracle union (compatible config set) | Regret | MAE rate | Top-3 | Bootstrap regret | Bootstrap MAE | Bootstrap top-3 |
|---|---|---|---|---:|---:|---:|---:|---|---|
| **14×60→12×80** | q3km_code_preplus + mx_q4km_code_attnq_q5k_plus | **48/80** | **56/80** (12-config) | **8.0** | **0.0630** | **0.0** | 5.25 [0, 13] | 0.0894 [0.0312, 0.2115] | 0.095 [0, 1] |
| **12×80→14×60** | gateup + mx2_aq6 | **34/60** | **39/60** (12-common) | **5.0** | **0.0630** | **0.0** | 4.45 [0, 11] | 0.0879 [0.0311, 0.1987] | 0.106 [0, 1] |
| **14×60→13×80 (KV8)** | — | **49/80** | **56/80** (13-config) | **7.0** | **0.0579** | **0.0** | — | — | — |
| **13×80→14×60 (KV8)** | — | **34/60** | **41/60** (13-config target) | **7.0** | **0.0579** | **0.0** | — | — | — |

**Notes.** 39/60 and 41/60 are best-pair unions on different compatible sets, 56/80 the source best-pair. The all-config oracle union is 58/80 and 43/60, so the selected-vs-all-config regret is 10 (48 vs 58) and 9 (34 vs 43); the table's regret is vs the best-pair oracle. Target-oracle point top-3 is 0.0; bootstrap 0.095/0.106, far below 0.90. KV8 adds 0 oracle/best-pair union (+1 selected union); boundary unchanged.

### 4.4 CP40 40-task panel

The panel uses 20 HumanEval+ + 20 MBPP+ unused (SHA `14161ce8…`); the remaining 60 MBPP+ stay sealed. Anchor 17/40, complement 15/40, union 18/40 (**+1**); b=1, c=0 (c=0 structural); one-sided exact McNemar p=0.5 (two-sided 1.0); CI [0,3] (seed 20261109); **INCONCLUSIVE**. HumanEval +1; MBPP 0 gain, **FAILURE**. CP@1 0.4199 global / 0.4190 nine; one timeout counted as failure. The panel is a screen.

### 4.5 Gemma second family

Gemma 4 E2B, 5 configs (he_dev 40, he_heldout 60, MBPP 60): exact headers 5 B/40, 8 B/60; within 0.00/0.00/1.00; split-half MAE 2.12/3.02/2.98; full-matrix best selected 0.572/0.507/0.276; selection coverage 0.176/0/0 (the source `cp1`); CP@1 not computed; target-best 0/6, regret 1–6. **Storage replicates exactly; transfer does not replicate numerically (failure).** The boundary is difficulty (truncation 17.6%; `GEMMA_CAP_AUDIT_PLAN.md`, `CROSS_FAMILY_BOUNDARY.md`), not fragility.

### 4.6 External selector

Within-sample, the exact header is unbeatable; MinHash-512 (2,048 B) ties the 14×60 selected-pair count/regret/top-3, not exactness (union MAE 0.0079), and is 256× larger. On the external-selector split (seed 20261109), the exact header is 1.70/3.45/0.080/0.047 and MinHash 1.45/3.26/0.150/0.120; Table 4.2 uses the full split. Random projection beats it on 12×80→14×60 regret/MAE (4 vs 5) but not top-3/selection coverage (no CP@1 certificate); L1 worse; no selector transfers the target-best. The exact header is a storage/audit artifact.

### 4.7 What the result says

The result is a **report-card** claim: exact within the observed matrix, not out-of-sample; the boundary tables/certificate detect the rest. MinHash is the within-sample fallback; Bloom/random projection fail.

## 5. Negative results as motivation

The V2 negative result motivates the storage question; the exact header makes it exact and the boundary auditable but does not make the V2 result positive.

## 6. Claims not made

- No new quantizer/SOTA/all-around win; no out-of-sample or cross-matrix exactness or near-oracle selection; exact for the observed pass set only.
- No claim that selection coverage is CP@1 (CP@1 0.6376/0.6532, MinHash 0.6376/0.6526; coverage 1.000/0.965, separate); no all-four estimate; no 8/10 B ablation; no replacement of full evaluation; no CP40 confirmation.

## 7. Limitations

The exactness is for the observed pass set only. Split-half 1.91/1.70 regret, 3.00/3.47 MAE, 0.208/0.079 top-3; cross-matrix/KV8/Gemma fail; CP40 inconclusive (MBPP subgroup flat); 8/10 B are per-matrix sizes. MinHash 100%/96.5% (top-3 1.00/0.99, coverage 1.000/0.965, CP@1 0.6376/0.6526); Bloom 71%/47%. The artifacts are public (GitHub release and Hugging Face model); DOI pending.

## 8. Conclusion

Behavioral report cards, not selectors. An 8-byte bitset holds 60 tasks; a 10-byte bitset holds 80. Within the observed matrix, the report card answers all pair/union queries exactly—0.00 regret, 0.0000 MAE, 1.00 top-3, selection coverage 1.000, CP@1 0.6376/0.6532, raw union 0.683/0.700—and the 31/60 complement contributes only 5 unique tasks, so the pair gain is 5, not 31. The header is not a selector. Out-of-sample, exactness does not transfer: split-half 1.91/1.70 regret, 3.00/3.47 MAE, 0.208/0.079 top-3 (40.5%/41.1% config stability); cross-matrix/KV8/CP40/Gemma fail; external selectors do not transfer the target-best. The certificate layer records the tested gaps. The claim is exact storage/audit for the observed matrix and an auditable transfer boundary, not near-oracle selection.

## Artifacts and references

- Prior negative result: `PAPER_DRAFT_V2.md`, `EXTERNAL_CRITIQUE_PAPER_V2_2026-11-09.md`.
- Evidence: the manifest is `harness/architect/queue/evidence/pass-set-header/` (**16 hashed evidence files + `SHA256SUMS` = 17 files**; manifest zip `de995174…`, manifest `SHA256SUMS` `35b31e8e…`); the staged bundle is `harness/architect/queue/evidence/behavioral-report-cards-v6/` (79/79 files; bundle `SHA256SUMS` `c8f2d8d0…`, zip `da336826…`); the release repo has the V12/essay (`behavioral-report-cards`, main (tag v12)). **Provenance: the source repository is private/404: `https://github.com/antonrosso34-maker/LLM-intagration` (main `a3bb980`, branch `team/architect-predictor` `be038a5…`); the public release is `https://github.com/antonrosso34-maker/behavioral-report-cards` (main (tag v12), data/evidence/paper); the Hugging Face model is `https://huggingface.co/AntonROSSO/qwen2.5-coder-1.5b-mx2-aq6-q3ks` (Apache-2.0, 750.3 MiB, SHA256 `7fe6c14d…`); the staged bundle is the copy above; no DOI is claimed.** 7 claims, no orphans; exact headers 8 B/60 and 10 B/80, lossless; MinHash 2,048 B (64-byte retracted); best pair 41/60 heldout, 56/80 fresh; Rule certificate EXACT-HEADER-01; task routing at chance (LOTO AUC 0.5612).
- Rule certificate: EXACT-HEADER-PAIR-01, \(\alpha = 0.05\), seed 20261109, \(B = 2000\), SHA-256 407f9587c57c99d7a68b90fc741b0ac11559817ce0642df19bc03f4fbbcd8273.
- Cross-matrix certificate: EXACT-HEADER-CROSS-01, \(\alpha = 0.05\), seed 20261109, \(B = 2000\), SHA-256 6c045220bf7b4a73cafd363ecbdec8b046255bab0e5ebfa5c7ae6a86b551f320.
- CP@1 certificate: `harness/architect/agents/09_benchmark/CP1_FEASIBILITY.md`; false-pass 18/269 = 6.69% [4.01, 10.37], 21/305 = 6.89% [4.31, 10.33], private 202/202 killed, LB 0.982; exact header CP@1 0.6376/0.6532; raw union 0.683/0.700; selection coverage 1.000 by construction (the 200-seed interval is for sketch comparators).
- New V6 evidence: `agents/04_routing/GEMMA_SECOND_FAMILY.md`, `V6_KV8_ANALYSIS.md`, `EXTERNAL_SELECTOR_BASELINE.md`; `agents/05_power/TRANSFER_CALIBRATION.md`; `agents/09_benchmark/evidence/cp40/cp40_analysis.md (completed panel)`; `harness/architect/queue/cp40/CP40_PLAN.md`.
- References: GPTQ (Frantar et al., arXiv:2210.17323, https://arxiv.org/abs/2210.17323); AWQ (Lin et al., arXiv:2306.00978, https://arxiv.org/abs/2306.00978); SpQR (Dettmers et al., arXiv:2306.03078); AMQ (arXiv:2509.12019, https://arxiv.org/abs/2509.12019); CompressionBench (arXiv:2611.06858, https://arxiv.org/abs/2611.06858); LLM-KICK (arXiv:2310.01382, https://arxiv.org/abs/2310.01382); ACBench (arXiv:2505.19433, https://arxiv.org/abs/2505.19433); HumanEval+ (Liu et al., arXiv:2305.01210); SWE-bench (Jimenez et al., arXiv:2310.06770); Report Cards (Yang et al., arXiv:2409.00844, NeurIPS 2024 SoLaR workshop spotlight); Evaluating Quantized LLMs (Li et al., ICML 2024, PMLR 235:28480-28524, arXiv:2402.18158); pass@1 (Chen et al., arXiv:2107.03374); MinHash (Broder, 1997, "On the resemblance and containment of documents"); Bloom filter (Bloom, 1970, CACM 13(7)); Qwen2.5-Coder (arXiv:2409.12186); Gemma 4 E2B (Google DeepMind, 2025; `MODEL_CARD.md`).

















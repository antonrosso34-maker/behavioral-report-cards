# Store the Pass Set, Not the Selector: Exact Behavioral Headers and the Transfer Boundary

**Status:** V5 draft for critique. Writing/design only. No scored run, server, lock, GPU, new session, or commit. The exact header is an exact storage artifact for the observed pass set; it is not out-of-sample or cross-matrix exact. The negative results are the prior V2 findings and motivate the work.

## Abstract

For a fixed evaluation matrix, quantization configuration selection is usually driven by weight error or perplexity, but deployment is judged by which tasks a configuration passes. The pass set itself is small enough to store **exactly**: 60 tasks fit in an **8-byte bitset**, 80 tasks in **10 bytes**. The header is a behavioral report card for the observed matrix: within-sample pair and union selection is **0.00 regret**, **0.0000 MAE**, **1.00 top-3**; selection coverage is **1.000 [0.982, 1.000]**; CP@1 (certified pass@1, false-pass-adjusted) is **0.6376/0.6532**; raw selected-pair union is **0.683/0.700**, with false-pass **18/269 = 6.69% [4.01, 10.37]** and **21/305 = 6.89% [4.31, 10.33]**, private 202/202 killed, lower bound **0.982**. The exactness does not transfer. A 50/50 split-half gives 14×60 **1.91 [0, 6]** regret, **3.00 tasks [1.15, 7.40]** union MAE, **0.208 [0, 1]** top-3; 12×80 **1.70 [0, 4]**, **3.47 [1.00, 8.97]**, **0.079 [0, 1]**. The **40.5%/41.1%** figure is configuration stability, not split-half. Cross-matrix also fails: 14×60→12×80 selects **48/80** vs **56/80** (regret **8.0**, top-3 **0.0**); 12×80→14×60 selects **34/60** vs the **39/60** common-config oracle (regret **5.0**, top-3 **0.0**); the target oracle has point top-3 **0.0** (bootstrap mean **0.095/0.106**, far below the 0.90 bar). MinHash-512 (2,048 B) meets the **regret+MAE** bars in **100%/96.5%**; top-3 **1.00/0.99**; selection coverage **1.000/0.965 [0.929, 0.986]**; CP@1 is **1.000/0.965**; the all-four intersection is unestimated. Bloom-512 meets the regret+MAE bars in **71%/47%** (top-3 **0.95/0.94**, selection coverage **0.905/0.935**), and CP@1 fails. The header is set-level only. The certificate layer detects the transfer boundary: Rule certificates EXACT-HEADER-PAIR-01 and EXACT-HEADER-CROSS-01. We claim exact storage for the observed matrix and an auditable transfer boundary, not near-oracle out-of-sample or cross-matrix selection.

## 1. Introduction

The prior V2 study found a split negative result: risk3 improved code-tail NLL over q4km_none and WikiText over q4km_code, but no in-house point was significantly better on both axes against the same public baseline; the evidence was local-only; and the code evaluation was a 10-task screen. Those negative results expose the missing primitive: a compact, auditable way to store the pass set without re-running every configuration.

This paper supplies that primitive and reports its boundary. A behavioral pass set is the set of probes a configuration passes. The exact representation is a bitset: 60 tasks in 8 bytes, 80 in 10. Because the bitset is the pass set, pair and union selection is exact **within the observed pass set**. The exactness does not survive a 50/50 split-half: the selection rule trained on one half does not recover the full-matrix best pair out-of-sample.

**Contributions.**

1. **Exact pass-set storage.** 8-byte bitset for 60 tasks, 10-byte for 80; one bit per task, no summary.
2. **Within-sample exactness.** 0.00 regret, 0.0000 MAE, 1.00 top-3; selection coverage 1.000 [0.982, 1.000]; CP@1 0.6376/0.6532; raw union 0.683/0.700; false-pass 18/269 = 6.69%, 21/305 = 6.89%, private 202/202 killed, LB 0.982; best pair 41/60 heldout, 56/80 fresh. Set-level only; task routing at chance (LOTO AUC 0.5612).
3. **Out-of-sample boundary.** Split-half 1.91/1.70 regret; 3.00 [1.15, 7.40]/3.47 [1.00, 8.97] MAE; 0.208 [0, 1]/0.079 [0, 1] top-3; 40.5%/41.1% config stability.
4. **Cross-matrix boundary.** 14×60→12×80 48/80 vs 56/80; 12×80→14×60 34/60 vs 39/60 common-config oracle; target oracle point top-3 0.0 (bootstrap mean 0.095/0.106).
5. **Secondary approximation and comparators.** MinHash-512 2,048 B: regret+MAE 100%/96.5%, top-3 1.00/0.99, selection coverage 1.000/0.965, CP@1 1.000/0.965, all-four unestimated. Bloom-512: 71%/47%, top-3 0.95/0.94, selection coverage 0.905/0.935, CP@1 fails. Bloom-64 and random projection fail.
6. **Certificate layer.** Probe passport, claim.cert, Rule CI, CP@1, and Rule certificates EXACT-HEADER-PAIR-01/CROSS-01 make the boundaries auditable.

## 2. Related work

GPTQ and AWQ established practical 4-bit weight-only quantization; SpQR pushes below 4 bits; llama.cpp k-quants provide per-tensor overrides; AMQ uses a quality predictor for mixed precision; CompressionBench, LLM-KICK, and ACBench show that perplexity and compression can miss capability. MinHash and Bloom are standard set sketches; we use MinHash-512 as the within-sample approximation and Bloom-512 as a matched-budget comparator. This is a storage/evidence contribution, not a new quantizer and not an out-of-sample selection claim.

## 3. Method

### 3.1 Behavioral pass sets and exact bitset

For each configuration \(c\), the pass set \(P_c\) is the set of probes it passes under a fixed protocol. The probe passport records task ID, prompt hash, seed, runtime, result, and timestamp, so \(P_c\) is reproducible without the transcript.

The exact representation is a bitset: **60 tasks = 8 bytes** (4 padding bits), **80 tasks = 10 bytes**. The 8/10-byte headers are per-matrix sizes, not an ablation, and are not derived from MinHash. The exact header is 256×/204.8× smaller than MinHash-512 and 8×/6.4× smaller than Bloom-512.

### 3.2 Secondary sketch and comparators

**MinHash-512** stores 512 31-bit minima at 4 bytes each = **2,048 B** (4,096 B as int64); the earlier 64-byte claim is retracted. It meets the regret+MAE bars in **100%/96.5%** of within-sample cases; top-3 **1.00/0.99**; selection coverage **1.000/0.965**; CP@1 is **1.000/0.965**; all-four unestimated. Its union MAE is 0.0079/0.0056, not zero.

**Bloom-512** is a 512-bit matched-budget comparator: 0.245/0.13 regret, 0.0222/0.0306 MAE, 0.95/0.94 top-3, meeting the regret+MAE bars in 71%/47%; selection coverage 0.905/0.935; CP@1 fails. **Bloom-64** and **random projection** at 8/10 B fail.

### 3.3 Selection, split-half, and cross-matrix

**Within-sample.** The bitset is the pass set, so the oracle pair/union is available without prediction: 0.00 regret, 0.0000 MAE, 1.00 top-3.

**Split-half.** A 50/50 task split selects on one half and evaluates on the other. The exact header does not make the rule out-of-sample exact; Rule certificate **EXACT-HEADER-PAIR-01** records the gap (\(\alpha = 0.05\), seed 20261109, \(B = 2000\), SHA-256 407f9587c57c99d7a68b90fc741b0ac11559817ce0642df19bc03f4fbbcd8273).

**Config stability.** The full-matrix best pair is the top pair in only 40.5%/41.1% of configuration resamples; best-pair union is 39.72 [37, 41]/54.84 [52, 56]. This is config-set stability, not split-half.

**Cross-matrix.** The full 14×60 best pair is not evaluable on 12×80 because KV8 is absent; the table uses 12 common configs. Rule certificate **EXACT-HEADER-CROSS-01** records the failure (\(\alpha = 0.05\), seed 20261109, \(B = 2000\), SHA-256 6c045220bf7b4a73cafd363ecbdec8b046255bab0e5ebfa5c7ae6a86b551f320).

**CP@1 bar.** The exact header's raw selected-pair union is 0.683/0.700; false-pass-adjusted CP@1 is 0.6376/0.6532; selection coverage is 1.000 [0.982, 1.000], separate from CP@1. False-pass is 18/269 = 6.69% [4.01, 10.37] (eight saved configs), 21/305 = 6.89% [4.31, 10.33] (nine-config reference), private 202/202 killed, LB 0.982. CP@1 is within-sample/matrix-level, not conformal, not out-of-sample.

### 3.4 Certificate layer

- **Probe passport.** Per-probe identity and execution record.
- **claim.cert.** Claim text, scope, estimand, point estimate, 95% CI, sign convention, evidence pointers, verifier, expiry.
- **Rule CI.** Bootstrap CI over tasks and configurations for the selection rule.
- **CP@1.** Certified pass@1: the false-pass-adjusted lower bound \(\mathrm{CP@1}=(1/N)\sum_i y_i s_i\), with the global certificate. It is within-sample/matrix-level, not conformal, not out-of-sample. Selection coverage (top-1 pair = true best) is 1.000 [0.982, 1.000], separate from CP@1.
- **Rule certificates.** EXACT-HEADER-PAIR-01 and EXACT-HEADER-CROSS-01 bind the exactness and the split-half/cross-matrix boundaries.

### 3.5 Use case: behavioral report card

For a fixed evaluation matrix, the header is a behavioral report card: the 8/10-byte bitset is the pass set, so audits and pair/union queries are exact and cheap. The header is not a selector. For a new matrix, the certificate says selection is not transferable; the header still stores the new pass set but does not predict which configuration to choose.

## 4. Results

### 4.1 Within-sample evidence table

| Representation | Size/config | Tasks | Pair regret | Union MAE | Top-3 | Best pair union | Selection coverage [95% CI] | CP@1 | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| **Exact bitset (14×60)** | **8 B** | 60 | **0.00** | **0.0000** | **1.00** | **41/60** | 1.000 [0.982, 1.000] | **0.6376** | verifies 0.05/0.10 |
| **Exact bitset (12×80)** | **10 B** | 80 | **0.00** | **0.0000** | **1.00** | **56/80** | 1.000 [0.982, 1.000] | **0.6532** | verifies 0.05/0.10 |
| MinHash-512 (14×60) | 2,048 B | 60 | 0.00 | 0.0079 | 1.00 | 41.0 mean | 1.000 [0.982, 1.000] | 1.000 | regret+MAE 100% |
| MinHash-512 (12×80) | 2,048 B | 80 | 0.045 | 0.0056 | 0.99 | 55.955 mean | 0.965 [0.929, 0.986] | 0.965 | regret+MAE 96.5% |
| Bloom-512 (14×60) | 512 bits | 60 | 0.245 | 0.0222 | 0.95 | — | 0.905 [0.856, 0.942] | fails | regret+MAE 71% |
| Bloom-512 (12×80) | 512 bits | 80 | 0.13 | 0.0306 | 0.94 | — | 0.935 [0.891, 0.965] | fails | regret+MAE 47% |
| Bloom-64 | 64 bits | 60/80 | fails | fails | fails | — | — | fails | fails |
| Random projection (14×60) | 8 B | 60 | 4.00 | 0.0555 | fails | — | — | fails | fails |
| Random projection (12×80) | 10 B | 80 | 2.00 | 0.0452 | fails | — | — | fails | fails |

**Notes.** Exact rows are constructions from the observed pass set; 8 B/10 B are per-matrix sizes, not an ablation. The exact header selects the true best pair (41/60 heldout, 56/80 fresh); MinHash's selected union mean is 41.0/55.955. Set-level only; task routing at chance (LOTO AUC 0.5612). MinHash meets the regret+MAE bars in 100%/96.5%; top-3 1.00/0.99; selection coverage 1.000/0.965; CP@1 1.000/0.965; all-four unestimated. Bloom meets the regret+MAE bars in 71%/47%; top-3 0.95/0.94; selection coverage 0.905/0.935; CP@1 fails. **CP@1 is certified pass@1 (false-pass-adjusted), not conformal; selection coverage is separate.** 40.5%/41.1% is config stability, not split-half.

### 4.2 Split-half and config stability

| Matrix | Regret [95% CI] | Union MAE [95% CI] | MAE rate | Top-3 [95% CI] |
|---|---:|---:|---:|---:|
| **14×60** | **1.91 [0, 6]** | **3.00 [1.15, 7.40]** | **0.100** | **0.208 [0, 1]** |
| **12×80** | **1.70 [0, 4]** | **3.47 [1.00, 8.97]** | **0.087** | **0.079 [0, 1]** |

Config stability: best-pair union 39.72 [37, 41]/54.84 [52, 56]; top-pair frequency 40.5%/41.1%. This is not split-half. The out-of-sample bars are not met.

### 4.3 Cross-matrix

| Direction | Selected pair | Selected union | Oracle union (common configs) | Regret | MAE rate | Top-3 | Bootstrap regret | Bootstrap MAE | Bootstrap top-3 |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| **14×60→12×80** | q3km_code_preplus + mx_q4km_code_attnq_q5k_plus | **48/80** | **56/80** | **8.0** | **0.0630** | **0.0** | 5.25 [0, 13] | 0.0894 [0.0312, 0.2115] | 0.095 [0, 1] |
| **12×80→14×60** | gateup + mx2_aq6 | **34/60** | **39/60** | **5.0** | **0.0630** | **0.0** | 4.45 [0, 11] | 0.0879 [0.0311, 0.1987] | 0.106 [0, 1] |

**Notes.** KV8 is absent from 12×80, so the 39/60 is the common-config oracle, not the full 14-config 41/60 oracle. The target oracle has point top-3 0.0; bootstrap mean 0.095/0.106, far below the 0.90 bar.

### 4.4 What the result says

The exact result is a **storage** claim: the observed pass set is small enough to store, and within-sample selection is exact. It is not an out-of-sample or cross-matrix selection claim. The split-half and cross-matrix tables are the boundaries; the certificate layer detects them. MinHash is the within-sample fallback; Bloom and random projection fail.

## 5. Negative results as motivation

The V2 study is the motivation, not the contribution: risk3 improved code-tail NLL over q4km_none and WikiText over q4km_code, but no in-house point was significantly better on both axes against the same public baseline; the evidence was local-only; and the code evaluation was a 10-task screen. The exact header does not make the V2 negative result positive; it makes the storage question exact and the selection boundary auditable.

## 6. Claims not made

- No new quantizer, no SOTA compression, no all-around win.
- No out-of-sample or cross-matrix exactness; exact for the observed pass set only.
- No near-oracle out-of-sample or cross-matrix selection.
- No claim that MinHash's 1.000/0.965 selection coverage is CP@1; CP@1 is 1.000/0.965.
- No claim that the all-four intersection is estimated; it is not.
- No claim that the 8 B vs 10 B difference is an ablation; they are per-matrix sizes.
- No claim that the header replaces full evaluation; it stores the pass set and is verified by the certificate.

## 7. Limitations

- Exact for the observed pass set only; no out-of-sample or cross-matrix transfer.
- Split-half: 1.91/1.70 regret; 3.00 [1.15, 7.40]/3.47 [1.00, 8.97] MAE; 0.208 [0, 1]/0.079 [0, 1] top-3; bars not met.
- 40.5%/41.1% is config stability, not split-half.
- Cross-matrix fails: 48/80 vs 56/80; 34/60 vs 39/60 common-config oracle; target oracle point top-3 0.0 (bootstrap mean 0.095/0.106); KV8 absent.
- 8 B/10 B are per-matrix sizes, not an ablation.
- MinHash meets regret+MAE 100%/96.5%; top-3 1.00/0.99; selection coverage 1.000/0.965; CP@1 1.000/0.965; all-four unestimated.
- CP@1 is certified pass@1 (false-pass-adjusted): 0.6376/0.6532 exact header; raw union 0.683/0.700; false-pass 18/269 = 6.69%, 21/305 = 6.89%, private 202/202 killed, LB 0.982; within-sample, not conformal, not out-of-sample.
- Bloom-512, Bloom-64, and random projection fail; the manifest is public at `https://github.com/antonrosso34-maker/LLM-intagration/tree/team/architect-predictor` (commit `be038a5bffdceb51af6e4aa09779aee7ec5c6cd3`); the 25 KB zip is local; DOI/release pending.
- V2 negative results are motivation, not a positive quality claim.

## 8. Conclusion

Store the exact pass set, and report the boundary. An 8-byte bitset holds 60 tasks; a 10-byte bitset holds 80. Within the observed pass set, pair and union selection is exact—0.00 regret, 0.0000 MAE, 1.00 top-3—selection coverage is 1.000 [0.982, 1.000], and CP@1 is 0.6376/0.6532; raw union is 0.683/0.700; false-pass is 18/269 = 6.69%, 21/305 = 6.89%, private 202/202 killed, LB 0.982. The header is a report card for a fixed matrix, not a selector. Out-of-sample, the exactness does not transfer: split-half 1.91/1.70 regret, 3.00/3.47 MAE, 0.208/0.079 top-3; 40.5%/41.1% is config stability. Cross-matrix fails: 48/80 vs 56/80; 34/60 vs 39/60 common-config oracle; target oracle point top-3 0.0 (bootstrap mean 0.095/0.106). The certificate layer detects both gaps. MinHash meets regret+MAE 100%/96.5% (top-3 1.00/0.99, selection coverage 1.000/0.965, CP@1 1.000/0.965); Bloom meets 71%/47% (top-3 0.95/0.94, selection coverage 0.905/0.935); Bloom-64 and random projection fail. The claim is exact storage for the observed pass set and an auditable transfer boundary, not near-oracle out-of-sample or cross-matrix selection.

## Artifacts and references

- Prior negative result: `PAPER_DRAFT_V2.md`, `EXTERNAL_CRITIQUE_PAPER_V2_2026-11-09.md`.
- Certificate layer: `NOVEL_IDEAS_2026-11-09.md`; synthesis outline: `SYNTHESIS_PAPER_OUTLINE.md`.
- Public manifest: `harness/architect/queue/evidence/pass-set-header/`; 17 files + `SHA256SUMS`; 7 claims, no orphans; exact headers 8 B/60 and 10 B/80, lossless; MinHash 2,048 B (64-byte retracted); best pair 41/60 heldout, 56/80 fresh; Rule certificate EXACT-HEADER-01; task routing at chance (LOTO AUC 0.5612); public commit `https://github.com/antonrosso34-maker/LLM-intagration/commit/be038a5bffdceb51af6e4aa09779aee7ec5c6cd3`; zip local; DOI/release pending.
- Rule certificate: EXACT-HEADER-PAIR-01, \(\alpha = 0.05\), seed 20261109, \(B = 2000\), SHA-256 407f9587c57c99d7a68b90fc741b0ac11559817ce0642df19bc03f4fbbcd8273.
- Cross-matrix certificate: EXACT-HEADER-CROSS-01, \(\alpha = 0.05\), seed 20261109, \(B = 2000\), SHA-256 6c045220bf7b4a73cafd363ecbdec8b046255bab0e5ebfa5c7ae6a86b551f320.
- CP@1 certificate: `harness/architect/agents/09_benchmark/CP1_FEASIBILITY.md`; false-pass 18/269 = 6.69% [4.01, 10.37], 21/305 = 6.89% [4.31, 10.33], private 202/202 killed, LB 0.982; exact header CP@1 0.6376/0.6532; raw union 0.683/0.700; selection coverage 1.000 [0.982, 1.000].
- Correction notes: `harness/architect/agents/04_routing/V5_CORRECTION.md`, `harness/architect/agents/09_benchmark/V4_SECTION_3_4_PATCH.md`.
- References inherited from V2; verify identifiers before submission: GPTQ (arXiv:2210.17323); AWQ (arXiv:2306.00978); SpQR (arXiv:2306.03078); AMQ (arXiv:2509.12019); CompressionBench (arXiv:2611.06858); LLM-KICK (arXiv:2310.01382); ACBench (arXiv:2505.19433); HumanEval+ (arXiv:2305.01210); SWE-bench (arXiv:2310.06770).

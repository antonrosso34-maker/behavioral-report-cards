# V6 Input: Transfer, Certificates, and Public Evidence

**Status:** Design input for V6. V5 is the current draft (`paper/PAPER_DRAFT_V5.md`); V4 is the prior draft. This file is not a paper and makes no result claim. Analysis/design only; no scored run, server, lock, GPU, new session, or commit.

---

## 1. What V5 establishes

- **Exact header:** 8 bytes per configuration for 60 tasks (4 padding bits; 14×60 matrix 112 B); 10 bytes per configuration for 80 tasks (12×80 matrix 120 B). Lossless, LSB-first, seed-free.
- **Within-sample:** 0.00 pair regret, 0.0000 union MAE, 1.00 top-3; selection coverage 1.000 [0.982, 1.000]; **raw selected-pair union 0.683/0.700**; **exact-header CP@1 (certified pass@1, false-pass-adjusted) 0.6376/0.6532**. Best pair 41/60 and 56/80; best fixed 36/60 and 49/80; oracle 43/60 and 58/80.
- **False-pass:** 18/269 = 6.69% [4.01, 10.37] on eight saved configs; 21/305 = 6.89% [4.31, 10.33] on nine-config reference; private 202/202 killed; lower bound 0.982.
- **Transfer boundary:** split-half 1.91/1.70 regret; 3.00 [1.15, 7.40]/3.47 [1.00, 8.97] MAE; 0.208 [0, 1]/0.079 [0, 1] top-3. The 40.5%/41.1% figure is **configuration stability**, not split-half. Cross-matrix fails: 14×60→12×80 selects 48/80 vs 56/80; 12×80→14×60 selects 34/60 vs 39/60 **common-config** oracle; target oracle point top-3 0.0 (bootstrap mean 0.095/0.106). KV8 is absent from 12×80.
- **Secondary:** MinHash-512 (2,048 B) meets **regret+MAE** bars in 100%/96.5%; top-3 1.00/0.99; **selection coverage 1.000/0.965**; **CP@1 0.6376 [0.491, 0.764] / 0.6526 [0.524, 0.763]** (false-pass-adjusted); all-four intersection unestimated. Bloom-512 meets regret+MAE 71%/47% (top-3 0.95/0.94; selection coverage 0.905/0.935; CP@1 fails). Bloom-64 and random projection fail.
- **Certificate layer:** probe passport, `claim.cert`, Rule CI, CP@1, Rule certificates `EXACT-HEADER-PAIR-01` and `EXACT-HEADER-CROSS-01`.
- **Public manifest:** `harness/architect/queue/evidence/pass-set-header/` (17 files + `SHA256SUMS`; exact headers, task IDs, pass matrices, pair unions, certificates, reproducer); public commit `https://github.com/antonrosso34-maker/LLM-intagration/commit/be038a5bffdceb51af6e4aa09779aee7ec5c6cd3`; 25 KB zip local; DOI/release pending.

## 2. Residual evidence for V6

| # | Gap | Why it matters | Minimum acceptable evidence |
|---|---|---|---|
| 1 | **Independent out-of-sample split** | Split-half reuses the matrix; cross-matrix changes task mix and common configs. Neither is a clean independent task/config split. | Precommit a held-out split not used in V5; report regret, MAE, top-3, best-pair selection. |
| 2 | **40-task CP@1 panel** | The panel is not in the manifest; CP@1 is within-sample/matrix-level. | **DONE (2026-11-09):** CP40 panel 20+20 (panel SHA `14161ce8…`, Merkle `bd1c8f8a…`); anchor 17/40, complement 15/40, union 18/40 (+1), b=1/c=0, exact one-sided p=0.5, paired CI [0,3], **INCONCLUSIVE**; HE +1 (p=0.5); MBPP 0 gain (**FAILURE**); CP@1 0.4199 global / 0.4190 nine-config; 1 anchor timeout. Does not confirm transfer. |
| 3 | **KV8-inclusive cross-matrix** | Full 14×60 best pair contains KV8 absent from 12×80; V5 uses 12 common configs. | **DONE (2026-11-09):** 13×80 matrix; KV8 23/40 HE dev + 22/40 MBPP dev; union 58/80, best pair 56/80 (KV8 adds **0** union); within-sample 10 B exact; split-half 1.73 regret/3.38 MAE/0.121 top-3/CP@1 0.051; cross-matrix 49/80 vs 56/80 and 34/60 vs 41/60 (regret 7, top-3 0); **boundary unchanged**. |
| 4 | **40-task HumanEval+/MBPP+** | V5 is storage/evidence, not a code-quality benchmark; the V2 code screen was 10 tasks. | **DONE (same CP40 panel):** HE +1/20 (p=0.5), MBPP 0/20 (**FAILURE**); no confirmation; the panel is a screen, not a parity benchmark. |
| 5 | **Second model family** | One Qwen matrix; storage may not transfer. | **DONE (2026-11-09):** Gemma E2B, 5 configs; exact headers 5 B/40, 8 B/60; within-sample 0.00 regret/0.00 MAE/1.00 top-3; split-half MAE 2.12/3.02/2.98 tasks (0.106/0.101/0.100), CP@1 0.176/0.000/0.000; cross-matrix target-best 0/6, regret 1–6 (heldout→MBPP 37/60 vs 38/60; MBPP→heldout 37/60 vs 43/60); Qwen was 5–8. Storage boundary replicates exactly; transfer replicates qualitatively, not numerically. |
| 6 | **External selector baseline** | V5 compares MinHash, Bloom, random projection; no public selector beyond these. | **DONE (2026-11-09):** within-sample exact header unbeatable; out-of-sample MinHash-512 beats it on 12×80 split-half (1.45/3.26/0.150/0.120 vs 1.70/3.45/0.080/0.047); random projection beats it on 12×80→14×60 regret/MAE (4 vs 5; 0.0323 vs 0.0630); L1 worse; cross-matrix no selector transfers (all top-3/CP@1 0/0). The exact header is a storage/audit artifact, not the best out-of-sample selector. |
| 7 | **Public zip/release/DOI** | The commit is public, but the 25 KB zip is local and no release/DOI exists; F3 remains partially open. | Upload the zip to a release/Zenodo/OSF, record the URL/DOI, and verify `SHA256SUMS`/17 files. |
| 8 | **All-four intersection** | V5 reports regret+MAE, top-3, CP@1 separately; the all-four intersection is unestimated. | Estimate the intersection or keep it explicitly unestimated. |
| 9 | **Certificate scope** | CP@1 (certified pass@1) is not selection coverage and not conformal. | State both definitions and report them separately in `CLAIM_MAP.json`/`claim.cert`. |

## 3. V6 success criteria

- Exact storage unchanged: 8/10 B, lossless, 112/120 B matrices.
- Independent out-of-sample and KV8-inclusive cross-matrix tests meet the precommitted bars; otherwise keep V5's negative boundary.
- CP@1 and selection coverage reported separately; no “both bars” shorthand unless the all-four intersection is estimated.
- 40-task benchmark and second family either pass or are recorded as negative; no SOTA/Pareto/quality claim.
- Public commit exists; the zip/release/DOI is recorded and `SHA256SUMS`/17 files are verified.
- No claim that the header replaces full evaluation or is a task-level router.

## 4. What V6 must not do

- Do not use **186.5 t/s or 185 t/s** as model throughput; those are AI-conversation rates, not llama.cpp measurements. If throughput is needed, run `llama-bench` on the pinned build and report pp512/tg128 with model hashes.
- Do not merge the within-sample zero with out-of-sample estimates.
- Do not call CP@1 conformal or out-of-sample.
- Do not call MinHash exact.
- Do not call the 8 B vs 10 B difference an ablation; they are 60-task and 80-task sizes.
- Do not call the 40.5%/41.1% figure split-half; it is configuration stability.
- Do not call the 39/60 cross target the full oracle; it is the common-config oracle.
- Do not publish a URL/commit that is not the verified manifest.

## 5. Next bounded actions

1. Freeze independent split and 40-task CP@1 panel before any run; record IDs, hashes, certificate seed.
2. Run KV8-inclusive cross-matrix and 40-task paired HumanEval+/MBPP+ confirmation on CPU.
3. Add one external selector baseline at matched bytes.
4. Replicate on a second family if the first two pass; otherwise stop and keep the negative boundary.
5. Update `CLAIM_MAP.json`, `claim.cert`, and public manifest; verify `SHA256SUMS`.
6. Draft V6 from V5 plus the new evidence only; preserve V5's exact-storage claim and its split-half/cross-matrix negative rows.

## 6. Second-family evidence (completed 2026-11-09)

- **Family/data:** Gemma E2B, 5 configs (`q3_mix`, `google_qat_q4_0`, `gp1_qat_requant`, `udq4_k_xl`, `udq2_k_xl`); splits he_dev 40, he_heldout 60, mbpp_heldout 60.
- **Exact headers:** 5 B/40 tasks and 8 B/60 tasks; within-sample 0.00 regret, 0.00 MAE, 1.00 top-3, CP@1 1.000.
- **Split-half:** MAE 2.12/3.02/2.98 tasks (0.106/0.101/0.100); CP@1 0.176/0.000/0.000.
- **Cross-matrix:** target-best pair selected 0/6 directions; regret 1–6 tasks; heldout→MBPP 37/60 vs 38/60 (regret 1); MBPP→heldout 37/60 vs 43/60 (regret 6); Qwen was 5–8.
- **Verdict:** the storage boundary replicates exactly; the transfer boundary replicates qualitatively, not numerically. The exact header is a second-family storage artifact, not a selector. File: `agents/04_routing/GEMMA_SECOND_FAMILY.md`.

## 7. Robust/prior selection (completed 2026-11-09, negative)

- **Robust 10th-percentile selection:** identical to the baseline cross-matrix (14×60→12×80 regret 8.0 tasks, top-3 0.0; 12×80→14×60 regret 5.0, top-3 0.0); split-half essentially unchanged (regret 0.0820/0.0573 vs 0.0791/0.0571; top-3 0.108/0.100 vs 0.106/0.098). The lower bound selects the same pair.
- **Prior shrinkage λ=0.25:** split-half MAE 0.1056/0.0891 → 0.0937/0.0792, but split-half top-3 falls 0.106/0.098 → 0.046/0.044; λ≥0.5 collapses (0.002/0.042). On the target with the source prior, λ=0.25 matches the target-only exact header (0.000 regret, 1.0 top-3) but cannot improve it; the target-only header is already exact.
- **Verdict:** no transfer improvement; the negative boundary is sharpened and robust to these rules. The prior’s MAE gain is an estimator result, not a selection win. File: `agents/05_power/TRANSFER_CALIBRATION.md`.

## 8. Use-case demo (completed 2026-11-09)

The report card reads the 14×60 exact headers and reports pass rates, unique tasks, all 91 pairwise unions/complementarity, regression flags against `q3km_code_kvq8_0_preplus`, best partners, and the certificate summary. Example: the best pair is `q3km_code_kvq8_0_preplus + mx_q4km_code_attnq_q5k_plus` at 41/60; the complement passes 31/60 on its own and loses 10 baseline passes, but only 5 of its 31 passes are outside the baseline, so the pair gain is **5, not 31**; a standalone ranking misses the best deployment pair. Files: `harness/architect/queue/report-card-demo/` (`REPORT_CARD_DEMO.md`, `report_card.py`, `report_card.json`, `REPORT_CARD.md`). Manifest task-ID files normalized to LF; final zip SHA-256 `de9951744236499cfdea62efae129b65465c004c9f7e61593c23719edbb948e9`; `SHA256SUMS` SHA-256 `35b31e8ef0028fd80a3b6e9714d58ad6b70cebb8841c89b796b82060dccdbc73` (the earlier `8fc04774…` and `fc64ae68…` zips are superseded; `README.md`/`PUBLISH.md` are metadata outside the zip, so the zip hash is detached and stable). Manifest commit `be038a5bffdceb51af6e4aa09779aee7ec5c6cd3` on branch `team/architect-predictor`, public at https://github.com/antonrosso34-maker/LLM-intagration/tree/team/architect-predictor; transfer bundle `pass-set-header-2026-11-09.bundle` SHA-256 `B818B144FB4EC556FBF31E39CB1A4AD7A468870236A76B3303CFD3CB07A2A40E`; DOI/release pending (the manifest files and reproducer are public in the repo; the 25 KB zip is local with SHA `de995174…`). This is the practical “so what” the critique asks for. No scored run.

## 9. KV8-inclusive cross-matrix (completed 2026-11-09, negative)

- 13×80 matrix (12×80 + KV8): q3km_code q8_0 HE dev 23/40, MBPP dev 22/40.
- Union 58/80, best pair 56/80; **KV8 adds 0 union**. Within-sample exact header 10 B/config: 0.00 regret/MAE, 1.00 top-3.
- Split-half: 1.73 regret, 3.38 MAE (0.0846), top-3 0.121, CP@1 0.051.
- Cross-matrix: 14×60→13×80 49/80 vs 56/80 (regret 7, MAE 0.0579, top-3 0, target-best 0); 13×80→14×60 34/60 vs 41/60 (regret 7, MAE 0.0579, top-3 0, target-best 0). The KV8-inclusive boundary is unchanged. File: `agents/04_routing/V6_KV8_ANALYSIS.md`.

## 10. CP40 40-task panel (completed 2026-11-09, inconclusive/failure)

- Split: 20 HumanEval+ unused + 20 MBPP+ unused; panel SHA `14161ce8…`, Merkle `bd1c8f8a…`; remaining 60 MBPP+ sealed, 2 reserve untouched.
- Anchor 17/40 (42.5%), complement 15/40 (37.5%), union 18/40 (+1); b=1, c=0; exact one-sided McNemar p=0.5, two-sided 1.0; paired CI [0,3]; **decision INCONCLUSIVE**.
- HumanEval 20: anchor 8, complement 6, union 9 (+1), p=0.5, INCONCLUSIVE. MBPP 20: anchor 9, complement 9, union 9 (0), **FAILURE**.
- CP@1 0.4199 global / 0.4190 nine-config (raw pair union 0.45; false-pass 6.69%/6.89%; 1 anchor timeout). The panel is a real-code-benchmark **transfer screen**, not a powered confirmation; it does **not** confirm the selection. The V6 negative boundary stands.

## 11. External selector baseline (completed 2026-11-09)

- Within-sample, the exact header is unbeatable (8/10 B: 0.00 regret, 0.0000 MAE, 1.00 top-3, CP@1 1.000); MinHash-512 (2,048 B) ties the 14×60 exactness but is 256× larger.
- Out-of-sample, the boundary is not absolute: MinHash-512 beats the exact header on the 12×80 split-half on all four metrics (regret 1.45 vs 1.70; MAE 3.26 vs 3.45 tasks; top-3 0.150 vs 0.080; CP@1 0.120 vs 0.047); random projection at 8/10 B beats it on 12×80→14×60 regret/MAE (4 vs 5; 0.0323 vs 0.0630) but not top-3/CP@1. The learned L1 selector (14 features, 7.5 B/config) is worse everywhere (14×60 3.38/8.48/0.050/0.010; 12×80 3.04/11.44/0.075/0.035; cross 7/7 regret, MAE 0.2521/0.3350).
- Cross-matrix, no selector selects or top-3s the target-best (all 0/0); the V6 transfer conclusion is unchanged. The exact header is a storage/audit artifact, not the best out-of-sample selector; the paper must not claim otherwise. File: `agents/04_routing/EXTERNAL_SELECTOR_BASELINE.md`.

No new sessions, GPU, Kaggle, or quantizer changes are requested by this input.

# Behavioral Report Cards, Not Selectors — V12 Public Evidence

This repository is the **V12 public release (data, evidence, paper)** for the paper **Store the Pass Set, Not the Selector: Exact Behavioral Headers and the Transfer Boundary** (the V6 successor to the behavioral-report-card draft). It is a clean subset of the research tree: it contains the frozen data, certificates, analysis outputs, paper drafts/design inputs, and the reproducer/demo scripts needed to verify the claims. It contains **no model weights, no raw model completions, no private/restricted data, and no internal agent notes**.

## Scoped claim

For a **fixed evaluation matrix**, an 8-byte exact pass-set header (60 tasks) or a 10-byte header (80 tasks) makes deployment audits and pair/union analysis exact and cheap. On Qwen 14×60 and 12×80, the exact header selects the true best pair (41/60 and 56/80); the report card shows that a complement passing 31/60 alone contributes only **5 unique tasks** outside the baseline, so the pair gain is **5, not 31**. On Gemma E2B, the storage boundary replicates exactly (5 B/40, 8 B/60; 0.00/0.00/1.00).

The **transfer boundary is negative**: split-half, cross-matrix, the KV8-inclusive 13×80 test, and the 40-task CP40 panel do not confirm out-of-sample selection. The exact header is a **report card, not a selector**. The external-selector baseline adds the nuance that MinHash-512 (2,048 B) can beat the exact header on some split-half metrics and random projection can beat it on some cross-matrix regret/MAE, but **no selector transfers the target-best pair**. CP@1 is certified pass@1 (false-pass-adjusted); selection coverage is a separate estimand.

## Contents

- `data/pass-set-header/` — the 17-file manifest (16 hashed evidence files + `SHA256SUMS`; `README.md`, `PUBLISH.md`, and `MANIFEST.md` are metadata excluded from the hash list): exact headers (8 B/60, 10 B/80), task IDs, pass matrices, pairwise unions, `CLAIM_MAP.json`, `CERTIFICATES.json`, the MinHash-512 secondary sketch, `build_manifest.py`, and `SHA256SUMS`.
- `data/report-card/` — the behavioral report-card demo (`report_card.py`, `report_card.json`, `REPORT_CARD.md`, `REPORT_CARD_DEMO.md`).
- `evidence/exact-header/` — exact-header evidence (MD, JSON, script).
- `evidence/rule-ci/` — Rule CI (MD, JSON, script).
- `evidence/cross-matrix/` — cross-matrix OOS (MD, JSON, script).
- `evidence/transfer-calibration/` — robust/prior selection, negative (MD, JSON, script).
- `evidence/cp1/` — CP@1 feasibility, exact-header CP@1, 40-task certificate template (MD, JSON, script).
- `evidence/gemma-second-family/` — Gemma E2B second-family evidence (MD, JSON, script).
- `evidence/external-selector/` — external selector baseline (MD, JSON, script).
- `evidence/kv8/` — KV8-inclusive cross-matrix plan/analysis/split/summaries.
- `evidence/cp40/` — CP40 20+20 panel plan/split/hashes/analysis/summaries.
- `paper/` — `PAPER_DRAFT_V12.md` (current), `ESSAY_DRAFT_V1.md`, `PAPER_DRAFT_V6.md`, `PAPER_DRAFT_V5.md`, `PAPER_DRAFT_V6_INPUT.md`, `NEXT_PAPER_INPUT.md`, `NEXT_PAPER_BRIEF.md`.
- `RELEASE_METADATA.md` / `RELEASE_METADATA.json` — DOI/release metadata; `RELEASE_READINESS.md` — verification and pending items.
- `README.md`, `SHA256SUMS`.

## Verify

```sh
cd data/pass-set-header && sha256sum -c SHA256SUMS
cd ../.. && sha256sum -c SHA256SUMS
```

`data/pass-set-header/SHA256SUMS` verifies the manifest data files; the top-level `SHA256SUMS` verifies every file in this public bundle (excluding itself). On Windows, use Git Bash or `Get-FileHash`/`Compare-Object`. The `build_manifest.py` and `report_card.py` are included for reproduction; see their headers for usage. The analysis scripts document the reported numbers; the frozen data and hashes are the authoritative artifacts.

## Key hashes and provenance

- Manifest zip (release asset): `pass-set-header-2026-11-09.zip`, SHA-256 `de9951744236499cfdea62efae129b65465c004c9f7e61593c23719edbb948e9`.
- Manifest `SHA256SUMS` SHA-256: `35b31e8ef0028fd80a3b6e9714d58ad6b70cebb8841c89b796b82060dccdbc73`.
- Source evidence commit: `be038a5bffdceb51af6e4aa09779aee7ec5c6cd3` (local object). The source repository is **private/404** (not a public URL); this repository is the public release at `https://github.com/antonrosso34-maker/behavioral-report-cards`.
- **Provenance status:** the public release is this repository (`https://github.com/antonrosso34-maker/behavioral-report-cards`, main (tag v12)); the source repo is private/404; the nested manifest's `Git remote: none configured` refers to the bridge worktree. The DOI is pending.
- The public bundle hash is in `SHA256SUMS`; the release zip SHA is reported with the release asset.

## Scope and limitations

- The within-sample zero is **exact by construction** for the observed pass set; it is not an out-of-sample predictor.
- **Transfer is negative:** split-half 14×60/12×80 gives 1.91/1.70-task regret, 3.00/3.47-task union MAE, 0.208/0.079 top-3; cross-matrix gives 5–8-task regret; KV8-inclusive 13×80 adds **0** union (regret 7, top-3 0); the CP40 panel gives anchor 17/40, complement 15/40, union 18/40 (+1), exact one-sided p=0.5, paired CI [0,3], **INCONCLUSIVE**; MBPP subgroup 0 gain (**failure**); CP@1 0.4199/0.4190; 1 anchor timeout.
- **External-selector nuance:** within-sample the exact header is unbeatable; out-of-sample MinHash-512 beats it on the 12×80 split-half (1.45/3.26/0.150/0.120 vs 1.70/3.45/0.080/0.047), random projection beats it on 12×80→14×60 regret/MAE (4 vs 5; 0.0323 vs 0.0630) but not top-3/CP@1; the learned L1 selector is worse; cross-matrix no selector transfers.
- The exact-header CP@1 is **0.6376/0.6532** (raw pair union 0.683/0.700; selection coverage 1.000/0.965 separate). The 40-task panel CP@1 is 0.4199/0.4190.
- The 8 B and 10 B headers are per-matrix sizes (60 vs 80 tasks), not an ablation.
- No model-quality, SOTA, compression, or Pareto claim; models and raw generations are not included.

## Paper files

- `paper/PAPER_DRAFT_V12.md` — current paper draft (V12); `paper/ESSAY_DRAFT_V1.md` — essay.
- `paper/PAPER_DRAFT_V5.md` — prior paper draft (V5).
- `paper/PAPER_DRAFT_V6_INPUT.md` — V6 design input (exact header, boundary, Gemma, KV8, CP40, external selector).
- `paper/NEXT_PAPER_INPUT.md` and `paper/NEXT_PAPER_BRIEF.md` — the behavioral report-card / deployment-audit paper design.

## License and status

License: to be specified by the author (the model weights are Apache-2.0; this release is the evidence/paper artifact). The model weights are not included; only SHA-256 references. Public benchmark task IDs and pass/fail matrices are included; raw model completions are not. No private or restricted data is included.

**Citation (placeholder):** Project Syntactic, “Behavioral Report Cards, Not Selectors: Exact Pass-Set Headers and the Transfer Boundary,” V12 draft, 2026. See `RELEASE_METADATA.md` for the release status; no DOI is claimed yet.








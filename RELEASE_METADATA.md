# Release metadata — behavioral-report-cards v1.1.1

**Status:** public release at `https://github.com/antonrosso34-maker/behavioral-report-cards` (tag v1.1.1); source repository **private/404**; DOI pending.
**Title:** Pass-Set Complementarity in Quantized Code Models: A Two-Family Audit with Size and Transfer Boundaries
**Version:** v1.1.1 (2026-11-11)
**Authors:** Anton Rosso
**License:** CC BY 4.0 (paper/data/evidence) + MIT (scripts); model weights Apache-2.0. See `LICENSE`.
**Repository reference (private/404; not a public URL):** https://github.com/antonrosso34-maker/LLM-intagration
**Source evidence commit (local object):** `be038a5bffdceb51af6e4aa09779aee7ec5c6cd3`; source repo private/404; not a public URL
**Bundle status:** public release v1.1.1 at tag v1.1.1; DOI pending.
**DOI:** pending; no DOI is claimed.
**Archive target:** user-selected (institutional repository, Zenodo, OSF, or equivalent); the
external archive action belongs to the user.

## Bundle contents

- `paper/FINAL_PAPER_DRAFT_V1.md` — final paper v1.1.1 (paper body 2,694 whitespace / 2,989 stricter); `paper/FINAL_PAPER_RELEASE_V1.md` / `.html` — full release document and presentation.
- `paper/PAPER_DRAFT_V12.md` — prior V12 paper.
- `paper/PAPER_DRAFT_V5.md`, `paper/PAPER_DRAFT_V6_INPUT.md`, `paper/NEXT_PAPER_INPUT.md`,
  `paper/NEXT_PAPER_BRIEF.md` — prior drafts and design inputs.
- `data/pass-set-header/` — the 17-file manifest: 16 hashed evidence files + `SHA256SUMS`;
  `README.md`, `PUBLISH.md`, and `MANIFEST.md` are metadata excluded from the hash list.
- `data/report-card/` — behavioral report-card demo and outputs.
- `evidence/` — exact-header, Rule CI, cross-matrix, transfer-calibration, CP@1, Gemma
  second-family, external-selector, KV8, CP40, and Gemma audit evidence.
- `evidence/gemma-audit/` — aggregate Gemma E2B audit evidence: pass matrices, task IDs, sanitized summaries, aggregate statistics, `SHA256SUMS`; no raw completions.
- `README.md` — bundle overview and scoped claim.
- `RELEASE_METADATA.md` / `RELEASE_METADATA.json` — this metadata.
- `RELEASE_READINESS.md` — bundle-local readiness and pending items (no self-referential hash).
- `SHA256SUMS` — top-level hash list for the bundle.

## Scoped claim

For a fixed evaluation matrix, an 8-byte exact pass-set header (60 tasks) or a 10-byte header
(80 tasks) makes deployment audits and pair/union analysis exact and cheap. The exactness does
not transfer out-of-sample; the paper reports the transfer boundary. There is no model-quality,
SOTA, compression, or Pareto claim.

## Final paper v1.1.1 (working draft)

- **Path:** `paper/FINAL_PAPER_DRAFT_V1.md`
- **Title:** Pass-Set Complementarity in Quantized Code Models: A Two-Family Audit with Size and Transfer Boundaries
- **Date:** 2026-11-11
- **Status:** final paper v1.1.1; paper body 2,694 words (whitespace; 2,989 stricter); full release document and styled HTML; outside the V6 hashed bundle.
- **Paper SHA-256:** `11eeaa5e296a6d83104f362b61a5d9eaf8ec7489e8925dfd030a0f80b75e0513`.
- **Release document:** `paper/FINAL_PAPER_RELEASE_V1.md` (SHA-256 `739bc80c377de3ce18b77144d9735eda34457d87b5e51b8415b5448b356efd6c`); **styled HTML:** `paper/FINAL_PAPER_RELEASE_V1.html` (SHA-256 `d03716d20596e0c09de0294c158767901ffff87be7631a734f72e5d19ea8c01b`).
- **Scope:** pass-set complementarity + two-family Gemma E2B audit. HumanEval pair 42/60 vs 36/60 (one-sided p=0.0352; partial credit +9.01 pp, p=0.027) at 2.17×; sealed MBPP 40/60 vs 40/60 tie; repair@1 44/60 vs 40/60 (p=0.0625, post-hoc); size-matched `gp1b_2498` dev +5 / heldout −2; cross-family 45/60 vs 36/60 (p=0.0059, 1.476×, HumanEval-only). No size-matched single-model win.
- **Citation:** Anton Rosso, “Pass-Set Complementarity in Quantized Code Models: A Two-Family Audit with Size and Transfer Boundaries,” final paper v1.1.1, 2026.

## Checksums

- Top-level `SHA256SUMS` SHA-256: `613613c70b206772694610b759a8bd1da86f9c2b3f7ce9a7776c30f43d92d98f` in `SHA256SUMS.sha256` (v1.1.1); the release metadata is outside the hash list.

## Exclusions

No model weights, raw model completions, private/restricted data, or internal agent notes are
included. Model files are referenced by SHA-256 only.

## Citation (placeholder)

Anton Rosso, “Pass-Set Complementarity in Quantized Code Models: A Two-Family Audit with Size and Transfer Boundaries,” final paper v1.1.1, 2026. Prior: “Store the Pass Set, Not the Selector: Exact Behavioral Headers and the Transfer Boundary,” V12 draft, 2026.

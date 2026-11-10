# Release metadata — behavioral-report-cards V6

**Status:** public release at `https://github.com/antonrosso34-maker/behavioral-report-cards` (main `69163c9` (tag v12)); source repository **private/404**; DOI pending.
**Title:** Behavioral Report Cards, Not Selectors: Exact Pass-Set Headers and the Transfer Boundary
**Version:** V6 draft (2026-11-10)
**Authors:** Project Syntactic / architect-predictor team
**License:** No license has been granted yet; the author must specify the license before public
release. Do not treat this bundle as licensed for reuse until then.
**Repository reference (private/404; not a public URL):** https://github.com/antonrosso34-maker/LLM-intagration
**Source evidence commit (local object):** `be038a5bffdceb51af6e4aa09779aee7ec5c6cd3`; source repo private/404; not a public URL
**Bundle status:** committed in the public release repository (main `69163c9` (tag v12)); DOI pending.
**DOI:** pending; no DOI is claimed.
**Archive target:** user-selected (institutional repository, Zenodo, OSF, or equivalent); the
external archive action belongs to the user.

## Bundle contents

- `paper/PAPER_DRAFT_V6.md` — current V6 paper.
- `paper/PAPER_DRAFT_V5.md`, `paper/PAPER_DRAFT_V6_INPUT.md`, `paper/NEXT_PAPER_INPUT.md`,
  `paper/NEXT_PAPER_BRIEF.md` — prior drafts and design inputs.
- `data/pass-set-header/` — the 17-file manifest: 16 hashed evidence files + `SHA256SUMS`;
  `README.md`, `PUBLISH.md`, and `MANIFEST.md` are metadata excluded from the hash list.
- `data/report-card/` — behavioral report-card demo and outputs.
- `evidence/` — exact-header, Rule CI, cross-matrix, transfer-calibration, CP@1, Gemma
  second-family, external-selector, KV8, and CP40 evidence.
- `README.md` — bundle overview and scoped claim.
- `RELEASE_METADATA.md` / `RELEASE_METADATA.json` — this metadata.
- `RELEASE_READINESS.md` — bundle-local readiness and pending items (no self-referential hash).
- `SHA256SUMS` — top-level hash list for the bundle.

## Scoped claim

For a fixed evaluation matrix, an 8-byte exact pass-set header (60 tasks) or a 10-byte header
(80 tasks) makes deployment audits and pair/union analysis exact and cheap. The exactness does
not transfer out-of-sample; the paper reports the transfer boundary. There is no model-quality,
SOTA, compression, or Pareto claim.

## Exclusions

No model weights, raw model completions, private/restricted data, or internal agent notes are
included. Model files are referenced by SHA-256 only.

## Citation (placeholder)

Project Syntactic, “Store the Pass Set, Not the Selector: Exact Behavioral Headers and the
Transfer Boundary,” V6 draft, 2026.





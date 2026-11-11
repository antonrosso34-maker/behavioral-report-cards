# Release readiness — v1.1.0

**Status:** public release at https://github.com/antonrosso34-maker/behavioral-report-cards (tag v1.1.0); source repository **private/404**; DOI pending.

- **Final paper:** `paper/FINAL_PAPER_DRAFT_V1.md` present (paper body 2,694 words whitespace / 2,989 stricter; under 3,000); figures in `paper/figures/` (Figures 1–4).
- **Release document/HTML:** `paper/FINAL_PAPER_RELEASE_V1.md` (SHA-256 `4752129a4b56a7082c223210979da88a462941048b42fe92def4f323243bea6e`); `paper/FINAL_PAPER_RELEASE_V1.html` (SHA-256 `4c25c6facbcedb1630422abe5f5ee7a0753ddb6eee1bccdadf38a0192d53b99c`).
- **Gemma audit evidence:** `evidence/gemma-audit/` present (23 hashed files; `SHA256SUMS`; pass matrices, task IDs, sanitized summaries, aggregate statistics; no raw completions).
- **V12 prior paper:** `paper/PAPER_DRAFT_V12.md` present.
- **Manifest:** `data/pass-set-header/SHA256SUMS` has 16 hashed evidence files; with `SHA256SUMS` itself the manifest is **17/17**.
- **Top-level:** `SHA256SUMS` verifies the data/paper/figures/evidence; the release metadata is outside the hash list; top-level hash `3a886e8c7ca4151ecc70a91025556699903dcd8d8854815b67739ba62ff3c6f7` is in `SHA256SUMS.sha256`.
- **Pending:** DOI. License is CC BY 4.0 (paper/data/evidence) + MIT (scripts); model weights Apache-2.0.

**One-line verdict:** Public release v1.1.0 live; final paper with figures, release document/HTML, and Gemma audit evidence included; 17/17 manifest; DOI pending.

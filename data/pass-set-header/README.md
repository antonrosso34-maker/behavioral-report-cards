# Pass-set header evidence (repository-backed)

**Access status:** public release at https://github.com/antonrosso34-maker/behavioral-report-cards (tag v12). Public release: https://github.com/antonrosso34-maker/behavioral-report-cards (tag v12); DOI pending.
**Git remote:** none configured (`git remote -v` empty)
**HEAD:** `tag v12 (9cac63d)`
**Manifest commit status:** committed in the public release (tag v12)
**SHA256SUMS SHA-256:** `35b31e8ef0028fd80a3b6e9714d58ad6b70cebb8841c89b796b82060dccdbc73`
**Bundle:** `pass-set-header-2026-11-09.zip`
**Bundle SHA-256:** `de9951744236499cfdea62efae129b65465c004c9f7e61593c23719edbb948e9`

**Detached-hash note.** `README.md` and `PUBLISH.md` are publishing metadata outside the zip.
The zip contains `MANIFEST.md`, `SHA256SUMS`, the exact headers, task IDs, pass matrices, pair
unions, claim map, certificates, and the reproducer. The zip SHA-256 is recorded here and in
the sibling `pass-set-header-2026-11-09.zip.sha256`.

**LF normalization.** The task-ID files are written with LF line endings so their recorded
newline hashes match the files. This changed `SHA256SUMS` and the bundle. The earlier
`fc64ae68…` zip and `34de702e…` SHA256SUMS, and the intermediate `8fc04774…` zip and
`0082cda2…` SHA256SUMS, are **superseded** by the values above.

**Demo.** `harness/architect/queue/report-card-demo/` contains `REPORT_CARD_DEMO.md`,
`report_card.py`, `report_card.json`, and `REPORT_CARD.md`.

This directory is a repository-backed evidence manifest, public release (tag v12). The
manifest records exact pass-set headers for the existing 14×60 and 12×80 matrices, plus the
MinHash-512 secondary approximation (2,048 B as uint32; the 64-byte claim is retracted). No
scored run, server, lock, GPU, new session, or commit was used to build it.




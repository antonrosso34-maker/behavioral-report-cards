# Publish checklist — exact pass-set header evidence

**Access status:** public release at https://github.com/antonrosso34-maker/behavioral-report-cards (tag v12). **No URL or DOI is claimed.**
**HEAD at packaging:** `11b7abbf59e03c3cdc26e4e008c3e3ea7b218668`
**SHA256SUMS SHA-256:** `35b31e8ef0028fd80a3b6e9714d58ad6b70cebb8841c89b796b82060dccdbc73`
**Bundle:** `pass-set-header-2026-11-09.zip`
**Bundle SHA-256:** `de9951744236499cfdea62efae129b65465c004c9f7e61593c23719edbb948e9`
**Sibling hash file:** `pass-set-header-2026-11-09.zip.sha256`

**Detached-hash design.** `README.md` and `PUBLISH.md` are publishing metadata outside the zip.
The zip contains `MANIFEST.md`, `SHA256SUMS`, and the evidence files; its SHA-256 is recorded
above and in the sibling `.sha256` file. Updating this metadata does not change the bundle.

**LF normalization and supersession.** The task-ID files are written with LF line endings so
their recorded newline hashes match the files. The earlier `fc64ae68…` zip and `34de702e…`
SHA256SUMS, and the intermediate `8fc04774…` zip and `0082cda2…` SHA256SUMS, are **superseded**
by the values above.

**Demo.** `harness/architect/queue/report-card-demo/` contains `REPORT_CARD_DEMO.md`,
`report_card.py`, `report_card.json`, and `REPORT_CARD.md`.

**Coverage note.** `SHA256SUMS` covers the evidence files and excludes `MANIFEST.md`,
`README.md`, `PUBLISH.md`, and `SHA256SUMS` itself as metadata. The zip includes `MANIFEST.md`
and `SHA256SUMS`; the metadata files remain outside the zip.

## Exact publish steps

1. **Verify the bundle.**
   ```
   sha256sum -c SHA256SUMS
   ```
   Compare the zip hash to `pass-set-header-2026-11-09.zip.sha256`.

2. **Commit the evidence directory.**
   ```
   git status --short -- harness/architect/queue/evidence/pass-set-header
   git add harness/architect/queue/evidence/pass-set-header
   git commit -m "Add exact pass-set header evidence manifest"
   git rev-parse HEAD
   ```
   The HEAD above is the pre-commit state; replace it in `MANIFEST.md`, `README.md`, and this
   file with the new commit hash before publication.

3. **Push (user action).**
   ```
   git remote -v
   ```
   There is currently **no remote configured** (`git remote -v` is empty). Add the user's
   remote and push:
   ```
   git remote add origin <USER_REPOSITORY_URL>
   git push -u origin <BRANCH>
   ```
   Do not claim a repository URL until the push succeeds.

4. **Archive (user action).**
   Create a release/archive from `pass-set-header-2026-11-09.zip` on the user's chosen
   service (institutional repository, Zenodo, OSF, or equivalent). Record the archive URL/DOI
   only after it is issued.

5. **Update the metadata after publication.**
   Replace the repository-local wording in `MANIFEST.md`, `README.md`, and this file with the
   actual repository URL, commit hash, and archive URL/DOI. Recompute `SHA256SUMS` and the zip
   only if the evidence files change; metadata edits do not change the detached bundle hash.

## External blocker

No git remote is configured, and no archive/DOI exists. The public URL/archive is the user's
repository/archive action; this manifest cannot create a remote, push, or mint a DOI. Until
then the correct status is **repository-backed manifest; public archive pending**.


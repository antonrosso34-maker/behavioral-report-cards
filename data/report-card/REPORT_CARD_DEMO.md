# Behavioral report card / regression audit — demo

**Status:** analysis/design only. No scored run, server, lock, GPU, new session, or commit.
**Source:** `harness/architect/queue/evidence/pass-set-header/` (repository-backed exact-header
manifest).
**Outputs:** `report_card.py`, `report_card.json`, `REPORT_CARD.md`.

## What this demo is

A practical "so what" layer for the exact pass-set header. It reads the 14×60 heldout exact
headers and turns them into a deployment-style report card:

- **Pass rate** per configuration (passes/60).
- **Unique tasks**: tasks passed by this configuration and by no other configuration.
- **Pairwise union / complementarity**: for every pair, the union, Jaccard overlap, and the
  union gain over the stronger single.
- **Regression audit** against the best fixed baseline (`q3km_code_kvq8_0_preplus`, 36/60):
  gained, lost, net, and a descriptive flag (`improvement`, `neutral`, `regression`,
  `severe_regression`).
- **Best partner** for each configuration by union.
- **Certificate summary**: rule `EXACT-HEADER-01` decision, claim status counts, orphan-claim
  check, and the heldout task-list hash.

The report is descriptive. The regression flags are not causal claims; they say how a
configuration's pass set compares with the baseline on this 60-task matrix.

## Example insight

The best pair is `q3km_code_kvq8_0_preplus` + `mx_q4km_code_attnq_q5k_plus` at **41/60
(68.3%)**, 5 tasks above the 36/60 best single. The complement
`mx_q4km_code_attnq_q5k_plus` passes 31/60 on its own and is a severe regression against the
baseline (10 baseline passes lost, 5 gained), yet **only 5 of its 31 passes are outside the
baseline** — exactly the pair gain. The practical lesson: the complement's value is its
off-baseline coverage, not its standalone pass rate. A report card that only ranked single
configurations would discard the best deployment pair.

## Files and reproduction

```
python harness/architect/queue/report-card-demo/report_card.py
```

- `report_card.py` — reads `headers_heldout_14x60.json`, `.bin`, the task-ID list, and the
  certificates; writes the JSON and Markdown report.
- `report_card.json` — full per-config and 91-pair data, certificate summary, example insight.
- `REPORT_CARD.md` — the sample human-readable report.

## Scope and limitations

- **Matrix:** 14 Qwen2.5-Coder-1.5B configurations × 60 HumanEval heldout tasks. This is the
  existing manifest matrix, not a new evaluation.
- **Baseline:** the best fixed configuration on this matrix. A different deployment baseline
  changes the regression flags.
- **Set-level only:** the report card summarizes pass sets and pair unions. It does not claim a
  per-task router; the task-level routing result remains at chance (`IDX-SET-01`).
- **Provenance:** the exact headers are 8 bytes/config for 60 tasks, LSB-first; the heldout
  task-list SHA-256 is `a5e68d95e7adf158d7b0617a154aff68c714ca2a9008343980c6a0af07bcff3f`.
  The manifest's `SHA256SUMS` covers the evidence files; `MANIFEST.md`, `PUBLISH.md`, and
  `SHA256SUMS` itself are metadata and excluded from that hash list.

# Repository-backed evidence manifest: exact pass-set headers

**Status:** public release at https://github.com/antonrosso34-maker/behavioral-report-cards (tag v12); DOI pending.
**Access status:** public; DOI pending.
**Git remote:** https://github.com/antonrosso34-maker/behavioral-report-cards (tag v12)
**HEAD:** tag v12
**Manifest commit status:** committed in the public release (tag v12)
**SHA256SUMS SHA-256:** `35b31e8ef0028fd80a3b6e9714d58ad6b70cebb8841c89b796b82060dccdbc73`. `SHA256SUMS` covers every file except `MANIFEST.md` and
itself; `MANIFEST.md`, `README.md`, and `PUBLISH.md` are metadata and excluded.
**Scope:** exact pass-set headers for the existing 14-configuration x 60-task HumanEval
heldout matrix and the 12-configuration x 80-task fresh matrix (HumanEval dev 40 + MBPP dev
40). The exact header is the primary artifact; MinHash-512 is a secondary approximation.

## 1. Exact header format

- Heldout: **8 bytes per configuration** (60 bits; the high 4 bits of byte 7 are zero).
- Fresh: **10 bytes per configuration** (80 bits).
- Bit order: LSB-first. Task `i` is byte `i//8`, bit `i%8`. The task order is the canonical
  newline-joined `dataset/split/task_id` order in `task_ids_*.txt`.
- The binary files concatenate the headers in the config order in the JSON metadata.
- Exact round-trip: decoding each header reproduces every source pass bit for all 14x60 and
  12x80 cells (`exact_roundtrip=true`).

## 2. Files

| File | Role | SHA-256 |
|---|---|---|
| `build_manifest.py` | Reproducer | `1b7d045a8c253543233cd7f8ec3764153554788aa14db3a4bab4dd0b49f14a32` |
| `headers_heldout_14x60.bin` | 14 x 8 B exact headers | `7caed93594c0dc9d50e6c8e5e0489512e74adaa8781b179ad9da9b05ee2a5a56` |
| `headers_fresh_12x80.bin` | 12 x 10 B exact headers | `6c44557c65fd7e96df131dcd8df8d2b52c730961595760995429c0f5d28e9352` |
| `headers_heldout_14x60.json` | Config keys, full SHAs, pass counts, header hex, task/matrix hashes | `2c499006387c37ffdc92f62216826b66841859db987555f171f8184e35eae064` |
| `headers_fresh_12x80.json` | Same for fresh | `cf8f94319fe2494f2eff27551a846680bf20ef3614403ccdac5fcf92e322da57` |
| `pass_matrix_heldout_14x60.csv` | Source pass matrix | `806b0cd76f399eed2523b3e52574d8afe01d586228b80773e22b009bf879bc8b` |
| `pass_matrix_fresh_12x80.csv` | Source pass matrix | `907a1fd15ecbe57b1302b2d41b0d4d2f8bce6c1586612527b4ebb584bfd27aec` |
| `pair_unions_heldout_14x60.csv` | All pair unions; best pair marked | `8a2d11730e2e5cba9d6764893230851e332e8f2b2ff85320eae23fb7b2c2dc4e` |
| `pair_unions_fresh_12x80.csv` | All pair unions; best pair marked | `6879afa7e40fb87ca906b487ffd8502bf9e819f955d450de3279a1c2229257bd` |
| `minhash_secondary.json` | MinHash-512/256 secondary metrics and 2,048 B correction | `11494960b899a28e923bd7096187b4ed9192bbf46c0879655af27e4896a27104` |
| `CLAIM_MAP.json` | Claim-to-artifact map; no orphan claims | `420da7cb50b2ce3cc683c8c85f47407c34893e1d110d2100ea7fd85a2689ff3d` |
| `CERTIFICATES.json` | Task, claim, rule, verifier certificates | `03301e65d015a20ae0550ec38baf56d613ce5d981b9becfc9b2861d30c65227e` |
| `SHA256SUMS` | Full hash list | `35b31e8ef0028fd80a3b6e9714d58ad6b70cebb8841c89b796b82060dccdbc73` |

Task ID files (`task_ids_heldout_14x60.txt/.json`, `task_ids_fresh_12x80.txt/.json`) are
included; their hashes are in `SHA256SUMS` and in the header metadata.

## 3. Positive result

- Heldout 14x60: best fixed **36/60**; oracle union **43/60**;
  best pair **q3km_code_kvq8_0_preplus + mx_q4km_code_attnq_q5k_plus = 41/60**.
- Fresh 12x80: best fixed **49/80**; oracle union **58/80**;
  best pair **mx2_aq6_q3ks_plus + mx_q3km_code_gateup_q4k_plus = 56/80**.
- The exact header selects the true best pair by construction (bitwise OR), with zero
  approximation error. The header is **set-level only**; task-level routing remains at chance
  (IDX-SET-01: LOTO AUC 0.5612).

## 4. MinHash correction

The MinHash-512 entry is **secondary**. It stores 512 31-bit minima: **2,048 bytes as uint32**
(4,096 as int64), not 64 bytes. The earlier 64-byte claim is retracted. The secondary metrics
are 0.00 regret / 0.0079 union MAE / 1.00 top-3 on 14x60, and 0.04 / 0.0056 / 0.99 on 12x80;
see `minhash_secondary.json`.

## 5. Commands

```
python harness/architect/queue/evidence/pass-set-header/build_manifest.py
python harness/architect/agents/04_routing/pass_set_sketch.py
git remote -v
git rev-parse HEAD
```

The first command regenerates the exact headers, matrices, pair tables, claim map, certificates,
and SHA256SUMS from `harness/architect/data/paired.csv` and `configs.csv`. The second
regenerates the MinHash secondary output. Verify with `sha256sum -c SHA256SUMS` (or
`Get-FileHash` on Windows).

## 6. Missing artifacts

- The **40-task CP@1 panel** was run on 2026-11-09 (see `harness/results/cp40/cp40_analysis.md` and the CP40 certificate); its task IDs and Merkle root are in the CP40 plan/analysis, not this manifest; the remaining 60 MBPP+ stay sealed.
- No full model SHA-256 is missing for the 14 heldout / 12 fresh configs. The `mx2_*` SHAs were
  computed from the local GGUF files; `q3km_code_kvq8_0_preplus` shares the `q3km_code` weights
  (same full SHA) and differs only by KV cache.
- The exact header is an encoding result over existing pass/fail cells; it is **not** a new
  evaluation and must not be presented as one.

## 7. Critique fix in this area

**F3 verifiability.** The manifest records full hashes, task IDs, exact headers, commands, and a
claim-to-artifact map. It is a **repository-backed manifest**, not yet a public artifact; the
public archive is pending and no URL/DOI is claimed. The 64-byte-vs-2,048-byte correction is the
kind of unit/provenance error the manifest is designed to catch.



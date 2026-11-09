#!/usr/bin/env python3
"""Build the public evidence manifest for the exact pass-set header result.

Reads the existing paired ledger and config table, reconstructs the 14x60
heldout and 12x80 fresh pass matrices, writes exact pass-set headers
(8 bytes / 60 tasks; 10 bytes / 80 tasks), task IDs, pair-union tables,
claim map, certificates, and SHA256SUMS.

Analysis-only: no model run, server, lock, GPU, or new session.
Writes only under this directory.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCH = HERE.parents[2]  # .../harness/architect
DATA = ARCH / "data"
PAIRED = DATA / "paired.csv"
CONFIGS = DATA / "configs.csv"
ROUTING = ARCH / "agents" / "04_routing"
SKETCH_OUT = ROUTING / "pass_set_sketch_output.json"
REPO = HERE.parents[4]


def git_info():
    def run(args):
        try:
            return subprocess.check_output(
                ["git", "-C", str(REPO)] + args,
                text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            return ""
    head = run(["rev-parse", "HEAD"]) or "unavailable"
    remotes = run(["remote", "-v"])
    remote_display = remotes.replace("\n", "; ") if remotes else "none configured (`git remote -v` empty)"
    status = run(["status", "--short", "--", str(HERE)])
    if "??" in status:
        manifest_status = "working-tree/untracked (not yet committed)"
    elif status:
        manifest_status = "working-tree changes (not yet committed)"
    else:
        manifest_status = "tracked and clean at HEAD"
    return {"head": head, "remote_display": remote_display, "manifest_status": manifest_status}

HELDOUT = [
    "q3km_none_plus", "q4km_code_plus", "q4ks_code_plus", "q3km_code_preplus",
    "q3km_code_kvq8_0_preplus", "q4km_code_preplus", "q3km_code_plus",
    "mx_q3km_code_attnq_q5k_plus", "mx_q3km_code_gateup_q4k_plus",
    "mx2_aq5_q3ks_plus", "mx2_aq6_q3ks_plus", "mx2_aq5_attnk5_plus",
    "mx_q4km_code_attnq_q5k_plus", "q3ks_code_plus",
]
FRESH = [
    "mx2_aq5_attnk5_plus", "mx2_aq5_q3ks_plus", "mx2_aq6_q3ks_plus",
    "mx_q3km_code_attnq_q5k_plus", "mx_q3km_code_gateup_q4k_plus",
    "mx_q4km_code_attnq_q5k_plus", "q3km_code_plus", "q3km_code_preplus",
    "q3km_none_plus", "q3ks_code_plus", "q4km_code_plus", "q4ks_code_plus",
]

FULL_SHA = {
    "q3km_none_plus": "06673dfdde81a2e376bf2639db8d1634afe889cffd511e4cbdfced92224472a5",
    "q4km_code_plus": "8aaee8e6e4346201baf983161afe58bc6f5a3c62ef431fc55a34dc676b604f91",
    "q4ks_code_plus": "2019ebc1048df16bbf667e672c7f54f75aa6d667329f7b4614b83bd4a9f0e3bb",
    "q3km_code_preplus": "fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb",
    "q3km_code_kvq8_0_preplus": "fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb",
    "q4km_code_preplus": "8aaee8e6e4346201baf983161afe58bc6f5a3c62ef431fc55a34dc676b604f91",
    "q3km_code_plus": "fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb",
    "mx_q3km_code_attnq_q5k_plus": "ae6412f35e48eccd2e1682980c5840eb141ef5b58fc542266a70cc68606c042a",
    "mx_q3km_code_gateup_q4k_plus": "5415d48fe261d18076bd10b63dce080975e11964b363188bc1c2207ea3de5480",
    "mx2_aq5_q3ks_plus": "99cf5eb7358027b86a095f2f31ddd51547bba77c8b2f6c072437be419e99013c",
    "mx2_aq6_q3ks_plus": "7fe6c14d18f64746a77262550853171a5465f8958482f75b69d034162bdd7e5c",
    "mx2_aq5_attnk5_plus": "5fc986e021d3bc686603f00ed4dc80387b62348e1e19656d1fe7252406e39c70",
    "mx_q4km_code_attnq_q5k_plus": "f03ecc3eeb5f957f1331aae886779730bbaa9f1825d1abd075fa894407760b74",
    "q3ks_code_plus": "d41b8c0cc619b0646d693ce7a17bc0def20374ddecf51b030dfcc70eadfa1283",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_cells():
    rows = [
        r for r in csv.DictReader(PAIRED.open(encoding="utf-8"))
        if r["family"] == "qwen2.5-coder-1.5b" and r["ref_pass"] != ""
    ]
    by = defaultdict(dict)
    for r in rows:
        by[r["config_name"]][(r["dataset"], r["split"], r["task_id"])] = int(r["passed"])
    return by


def load_config_rows():
    return {r["config_name"]: r for r in csv.DictReader(CONFIGS.open(encoding="utf-8"))}


def tasks_for(by, names, splits):
    common = set.intersection(*[
        {t for t in by[c] if (t[0], t[1]) in splits} for c in names
    ])
    return sorted(common)


def matrix_for(by, names, tasks):
    return [[by[c][t] for t in tasks] for c in names]


def task_id(t):
    return f"{t[0]}/{t[1]}/{t[2]}"


def pack_header(bits):
    n = len(bits)
    out = bytearray((n + 7) // 8)
    for i, b in enumerate(bits):
        if b:
            out[i // 8] |= 1 << (i % 8)
    return bytes(out)


def unpack_header(data: bytes, n: int):
    return [(data[i // 8] >> (i % 8)) & 1 for i in range(n)]


def pair_rows(names, M):
    n = len(M[0])
    rows = []
    best = None
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            union = sum(1 for k in range(n) if M[i][k] or M[j][k])
            rows.append({
                "pair_a": names[i],
                "pair_b": names[j],
                "union_tasks": union,
                "union_rate": round(union / n, 6),
                "best": False,
            })
            if best is None or union > best[0]:
                best = (union, i, j)
    for r in rows:
        if r["pair_a"] == names[best[1]] and r["pair_b"] == names[best[2]]:
            r["best"] = True
    rows.sort(key=lambda r: (-r["union_tasks"], r["pair_a"], r["pair_b"]))
    return rows, best


def write_pair_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["pair_a", "pair_b", "union_tasks", "union_rate", "best"])
        w.writeheader()
        w.writerows(rows)


def build_one(label, names, tasks, M, config_rows, header_bytes):
    n = len(tasks)
    ids = [task_id(t) for t in tasks]
    ids_txt = "\n".join(ids) + "\n"
    ids_json = json.dumps(ids, separators=(",", ":")) + "\n"
    (HERE / f"task_ids_{label}.txt").write_bytes(ids_txt.encode("utf-8"))
    (HERE / f"task_ids_{label}.json").write_bytes(ids_json.encode("utf-8"))

    headers = []
    config_entries = []
    for name, row in zip(names, M):
        hdr = pack_header(row)
        assert len(hdr) == header_bytes, (label, name, len(hdr), header_bytes)
        assert unpack_header(hdr, n) == row, (label, name, "roundtrip")
        headers.append(hdr)
        cfg = config_rows[name]
        config_entries.append({
            "config_name": name,
            "config_key": cfg["config_key"],
            "full_sha256": FULL_SHA[name],
            "size_mb": float(cfg["size_mb"]),
            "base": cfg["base"],
            "calibration": cfg["calibration"],
            "plus_test": int(cfg["plus_test"]),
            "pass_count": int(sum(row)),
            "header_hex": hdr.hex(),
        })

    bin_path = HERE / f"headers_{label}.bin"
    bin_path.write_bytes(b"".join(headers))

    # Canonical matrix hash: rows joined by newline, cells by comma.
    canonical = "\n".join(",".join(str(x) for x in row) for row in M).encode()
    matrix_sha = sha256_bytes(canonical)

    # CSV matrix with a header row.
    csv_path = HERE / f"pass_matrix_{label}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["config_key", "config_name", "size_mb", "pass_count"] + ids)
        for cfg, row in zip(config_entries, M):
            w.writerow([cfg["config_key"], cfg["config_name"], cfg["size_mb"], cfg["pass_count"]] + row)

    pairs, best = pair_rows(names, M)
    pair_path = HERE / f"pair_unions_{label}.csv"
    write_pair_csv(pair_path, pairs)

    best_fixed = max(sum(row) for row in M)
    oracle_union = sum(1 for k in range(n) if any(M[i][k] for i in range(len(M))))
    meta = {
        "dataset": label,
        "source": str(PAIRED),
        "source_sha256": sha256_file(PAIRED),
        "n_configs": len(names),
        "n_tasks": n,
        "header_bytes_per_config": header_bytes,
        "bit_order": "LSB-first: task i -> byte i//8, bit i%8; unused high bits are zero",
        "task_list_sha256_newline": sha256_bytes(ids_txt.encode()),
        "task_list_sha256_json": sha256_bytes(ids_json.encode()),
        "matrix_sha256_canonical": matrix_sha,
        "header_bin_sha256": sha256_file(bin_path),
        "header_bin_bytes": bin_path.stat().st_size,
        "best_fixed": best_fixed,
        "oracle_union": oracle_union,
        "best_pair": [names[best[1]], names[best[2]]],
        "best_pair_union": best[0],
        "best_pair_rate": round(best[0] / n, 6),
        "exact_roundtrip": True,
        "configs": config_entries,
    }
    (HERE / f"headers_{label}.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    return meta, pairs


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    by = load_cells()
    config_rows = load_config_rows()

    h_tasks = tasks_for(by, HELDOUT, {("humaneval", "heldout")})
    h_M = matrix_for(by, HELDOUT, h_tasks)
    h_meta, h_pairs = build_one("heldout_14x60", HELDOUT, h_tasks, h_M, config_rows, 8)

    f_tasks = tasks_for(by, FRESH, {("humaneval", "dev"), ("mbpp", "dev")})
    f_M = matrix_for(by, FRESH, f_tasks)
    f_meta, f_pairs = build_one("fresh_12x80", FRESH, f_tasks, f_M, config_rows, 10)

    sketch = json.loads(SKETCH_OUT.read_text(encoding="utf-8"))
    minhash = {
        "status": "SECONDARY_APPROXIMATION",
        "method": "MinHash",
        "storage": {
            "k": 512,
            "encoding": "uint32 minima",
            "bytes_per_config": 2048,
            "int64_bytes_per_config": 4096,
            "note": "The earlier 64-byte claim is retracted. 512 31-bit minima = 2048 bytes as uint32; the exact header is the primary artifact.",
        },
        "heldout": sketch["heldout"]["minhash_512"],
        "fresh": sketch["fresh"]["minhash_512"],
        "heldout_minhash_256": sketch["heldout"]["minhash_256"],
        "fresh_minhash_256": sketch["fresh"]["minhash_256"],
        "source": str(SKETCH_OUT),
        "source_sha256": sha256_file(SKETCH_OUT),
    }
    (HERE / "minhash_secondary.json").write_text(
        json.dumps(minhash, indent=2) + "\n", encoding="utf-8"
    )

    # Hash the data artifacts before writing the claim map and certificates.
    data_files = [
        "task_ids_heldout_14x60.txt", "task_ids_heldout_14x60.json",
        "task_ids_fresh_12x80.txt", "task_ids_fresh_12x80.json",
        "headers_heldout_14x60.bin", "headers_heldout_14x60.json",
        "headers_fresh_12x80.bin", "headers_fresh_12x80.json",
        "pass_matrix_heldout_14x60.csv", "pass_matrix_fresh_12x80.csv",
        "pair_unions_heldout_14x60.csv", "pair_unions_fresh_12x80.csv",
        "minhash_secondary.json",
    ]
    hashes = {f: sha256_file(HERE / f) for f in data_files}

    claims = {
        "no_orphan_claims": True,
        "orphan_claims": [],
        "claims": [
            {
                "id": "C1",
                "claim": "Exact pass-set headers are lossless: 8 bytes for 60 tasks and 10 bytes for 80 tasks; decoding reproduces every source pass bit.",
                "status": "SUPPORTED",
                "artifacts": ["headers_heldout_14x60.bin", "headers_heldout_14x60.json", "headers_fresh_12x80.bin", "headers_fresh_12x80.json", "pass_matrix_heldout_14x60.csv", "pass_matrix_fresh_12x80.csv"],
                "evidence": "exact_roundtrip=true for all 14x60 and 12x80 cells",
            },
            {
                "id": "C2",
                "claim": "The exact header selects the true best pair: 41/60 on heldout and 56/80 on fresh.",
                "status": "SUPPORTED",
                "artifacts": ["pair_unions_heldout_14x60.csv", "pair_unions_fresh_12x80.csv", "headers_heldout_14x60.json", "headers_fresh_12x80.json"],
                "evidence": f"heldout best pair {h_meta['best_pair']} = {h_meta['best_pair_union']}/60; fresh best pair {f_meta['best_pair']} = {f_meta['best_pair_union']}/80",
            },
            {
                "id": "C3",
                "claim": "MinHash-512 is a secondary approximation: 0.00 regret / 0.0079 union MAE / 1.00 top-3 on 14x60; 0.04 / 0.0056 / 0.99 on 12x80.",
                "status": "SUPPORTED_SECONDARY",
                "artifacts": ["minhash_secondary.json"],
                "evidence": "pass_set_sketch_output.json minhash_512 cells",
            },
            {
                "id": "C4",
                "claim": "The MinHash-512 storage claim is 2,048 bytes as uint32 (4,096 as int64), not 64 bytes; the 64-byte claim is retracted.",
                "status": "CORRECTED",
                "artifacts": ["minhash_secondary.json"],
                "evidence": "512 31-bit minima x 4 bytes",
            },
            {
                "id": "C5",
                "claim": "Bloom is worse than MinHash at the same bit budget on these small pass sets.",
                "status": "SUPPORTED_SECONDARY",
                "artifacts": ["minhash_secondary.json"],
                "evidence": "pass_set_sketch_output.json bloom cells",
            },
            {
                "id": "C6",
                "claim": "The header is set-level only; task-level routing remains at chance.",
                "status": "SUPPORTED_SCOPE",
                "artifacts": ["headers_heldout_14x60.json"],
                "evidence": "IDX-SET-01 fresh result: LOTO AUC 0.5612; do not claim a task router",
            },
            {
                "id": "C7",
                "claim": "The exact header plus the certificate layer is reproducible from repository-backed artifacts.",
                "status": "SUPPORTED",
                "artifacts": ["build_manifest.py", "CERTIFICATES.json"],
                "evidence": "build_manifest.py regenerates all headers and hashes",
            },
        ],
    }
    certificates = {
        "rule_certificate": {
            "id": "EXACT-HEADER-01",
            "claim": "Exact pass-set headers are lossless and select the true best pair on the existing 14x60 and 12x80 matrices.",
            "pre_registered_rule": {
                "encoding": "8 bytes for 60 tasks; 10 bytes for 80 tasks; LSB-first; unused high bits zero",
                "success": "decoded header equals the source pass matrix for every config/task; pair union from headers equals source pair union",
                "failure": "any bit mismatch, hash mismatch, or task-list mismatch",
                "scope": "existing 14x60 heldout and 12x80 fresh matrices; no new scored run",
            },
            "observed": {
                "heldout": {
                    "configs": h_meta["n_configs"], "tasks": h_meta["n_tasks"],
                    "header_bytes": h_meta["header_bytes_per_config"],
                    "best_pair": h_meta["best_pair"], "best_pair_union": h_meta["best_pair_union"],
                    "best_fixed": h_meta["best_fixed"], "oracle_union": h_meta["oracle_union"],
                    "exact_roundtrip": h_meta["exact_roundtrip"],
                },
                "fresh": {
                    "configs": f_meta["n_configs"], "tasks": f_meta["n_tasks"],
                    "header_bytes": f_meta["header_bytes_per_config"],
                    "best_pair": f_meta["best_pair"], "best_pair_union": f_meta["best_pair_union"],
                    "best_fixed": f_meta["best_fixed"], "oracle_union": f_meta["oracle_union"],
                    "exact_roundtrip": f_meta["exact_roundtrip"],
                },
            },
            "decision": "SUCCESS",
            "replay": "python harness/architect/queue/evidence/pass-set-header/build_manifest.py",
        },
        "task_certificate": {
            "heldout": {
                "n_tasks": h_meta["n_tasks"],
                "task_list_sha256_newline": h_meta["task_list_sha256_newline"],
                "task_list_sha256_json": h_meta["task_list_sha256_json"],
                "source": h_meta["source"],
                "source_sha256": h_meta["source_sha256"],
            },
            "fresh": {
                "n_tasks": f_meta["n_tasks"],
                "task_list_sha256_newline": f_meta["task_list_sha256_newline"],
                "task_list_sha256_json": f_meta["task_list_sha256_json"],
                "source": f_meta["source"],
                "source_sha256": f_meta["source_sha256"],
            },
        },
        "claim_certificates": claims["claims"],
        "verifier_certificate": {
            "verifier": "harness/architect/data/paired.csv plus-test labels",
            "source_sha256": sha256_file(PAIRED),
            "timeout_rule": "not applicable: labels are existing; no new tests",
            "note": "The exact header is an encoding result over existing pass/fail cells, not a new evaluation.",
        },
    }
    (HERE / "CERTIFICATES.json").write_text(
        json.dumps(certificates, indent=2) + "\n", encoding="utf-8"
    )

    # Attach hashes to claim artifacts, including the reproducer and certificates.
    extra = {
        "build_manifest.py": sha256_file(HERE / "build_manifest.py"),
        "CERTIFICATES.json": sha256_file(HERE / "CERTIFICATES.json"),
    }
    for c in claims["claims"]:
        c["artifact_sha256"] = {a: hashes[a] for a in c["artifacts"] if a in hashes}
        for a in c["artifacts"]:
            if a in extra:
                c["artifact_sha256"][a] = extra[a]
    (HERE / "CLAIM_MAP.json").write_text(
        json.dumps(claims, indent=2) + "\n", encoding="utf-8"
    )

    # Key hashes for the manifest table.
    key_hashes = {
        "build_manifest.py": sha256_file(HERE / "build_manifest.py"),
        "headers_heldout_14x60.bin": hashes["headers_heldout_14x60.bin"],
        "headers_fresh_12x80.bin": hashes["headers_fresh_12x80.bin"],
        "headers_heldout_14x60.json": hashes["headers_heldout_14x60.json"],
        "headers_fresh_12x80.json": hashes["headers_fresh_12x80.json"],
        "pass_matrix_heldout_14x60.csv": hashes["pass_matrix_heldout_14x60.csv"],
        "pass_matrix_fresh_12x80.csv": hashes["pass_matrix_fresh_12x80.csv"],
        "pair_unions_heldout_14x60.csv": hashes["pair_unions_heldout_14x60.csv"],
        "pair_unions_fresh_12x80.csv": hashes["pair_unions_fresh_12x80.csv"],
        "minhash_secondary.json": hashes["minhash_secondary.json"],
        "CLAIM_MAP.json": sha256_file(HERE / "CLAIM_MAP.json"),
        "CERTIFICATES.json": sha256_file(HERE / "CERTIFICATES.json"),
    }

    git = git_info()

    # SHA256SUMS excludes metadata files (MANIFEST.md, README.md, PUBLISH.md) and itself.
    files = sorted([
        p for p in HERE.iterdir()
        if p.is_file() and p.name not in {"SHA256SUMS", "MANIFEST.md", "PUBLISH.md", "README.md"}
    ])
    lines = [f"{sha256_file(p)}  {p.name}" for p in files]
    (HERE / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sums_hash = sha256_file(HERE / "SHA256SUMS")

    manifest = f"""# Repository-backed evidence manifest: exact pass-set headers

**Status:** repository-backed manifest; URL/commit/archive pending. **Not yet a public artifact.**
**Access status:** repository-local; public archive pending. No URL or DOI is claimed.
**Git remote:** {git['remote_display']}
**HEAD:** `{git['head']}`
**Manifest commit status:** {git['manifest_status']}
**SHA256SUMS SHA-256:** `{sums_hash}`. `SHA256SUMS` covers every file except `MANIFEST.md` and
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
| `build_manifest.py` | Reproducer | `{key_hashes['build_manifest.py']}` |
| `headers_heldout_14x60.bin` | 14 x 8 B exact headers | `{key_hashes['headers_heldout_14x60.bin']}` |
| `headers_fresh_12x80.bin` | 12 x 10 B exact headers | `{key_hashes['headers_fresh_12x80.bin']}` |
| `headers_heldout_14x60.json` | Config keys, full SHAs, pass counts, header hex, task/matrix hashes | `{key_hashes['headers_heldout_14x60.json']}` |
| `headers_fresh_12x80.json` | Same for fresh | `{key_hashes['headers_fresh_12x80.json']}` |
| `pass_matrix_heldout_14x60.csv` | Source pass matrix | `{key_hashes['pass_matrix_heldout_14x60.csv']}` |
| `pass_matrix_fresh_12x80.csv` | Source pass matrix | `{key_hashes['pass_matrix_fresh_12x80.csv']}` |
| `pair_unions_heldout_14x60.csv` | All pair unions; best pair marked | `{key_hashes['pair_unions_heldout_14x60.csv']}` |
| `pair_unions_fresh_12x80.csv` | All pair unions; best pair marked | `{key_hashes['pair_unions_fresh_12x80.csv']}` |
| `minhash_secondary.json` | MinHash-512/256 secondary metrics and 2,048 B correction | `{key_hashes['minhash_secondary.json']}` |
| `CLAIM_MAP.json` | Claim-to-artifact map; no orphan claims | `{key_hashes['CLAIM_MAP.json']}` |
| `CERTIFICATES.json` | Task, claim, rule, verifier certificates | `{key_hashes['CERTIFICATES.json']}` |
| `SHA256SUMS` | Full hash list | `{sums_hash}` |

Task ID files (`task_ids_heldout_14x60.txt/.json`, `task_ids_fresh_12x80.txt/.json`) are
included; their hashes are in `SHA256SUMS` and in the header metadata.

## 3. Positive result

- Heldout 14x60: best fixed **{h_meta['best_fixed']}/60**; oracle union **{h_meta['oracle_union']}/60**;
  best pair **{h_meta['best_pair'][0]} + {h_meta['best_pair'][1]} = {h_meta['best_pair_union']}/60**.
- Fresh 12x80: best fixed **{f_meta['best_fixed']}/80**; oracle union **{f_meta['oracle_union']}/80**;
  best pair **{f_meta['best_pair'][0]} + {f_meta['best_pair'][1]} = {f_meta['best_pair_union']}/80**.
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

- The **40-task CP@1 panel** task IDs and Merkle root are **not** in this manifest; the panel is
  a future run and must commit its own split before execution.
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
"""
    (HERE / "MANIFEST.md").write_text(manifest, encoding="utf-8")
    print(f"wrote {len(files)} hashed evidence files + MANIFEST.md + SHA256SUMS under {HERE}")


if __name__ == "__main__":
    main()

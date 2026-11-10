#!/usr/bin/env python3
"""Behavioral report card / regression audit demo for the 14 Qwen configs.

Reads the exact pass-set headers from the repository-backed evidence manifest and
writes report_card.json and REPORT_CARD.md. Analysis-only; no model run.
"""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / "pass-set-header"
META = EVIDENCE / "headers_heldout_14x60.json"
HEADERS = EVIDENCE / "headers_heldout_14x60.bin"
TASKS = EVIDENCE / "task_ids_heldout_14x60.txt"
CERTS = EVIDENCE / "CERTIFICATES.json"
CLAIMS = EVIDENCE / "CLAIM_MAP.json"
BASELINE = "q3km_code_kvq8_0_preplus"


def load():
    meta = json.loads(META.read_text(encoding="utf-8"))
    raw = HEADERS.read_bytes()
    n = meta["n_tasks"]
    width = meta["header_bytes_per_config"]
    tasks = [line.strip() for line in TASKS.read_text(encoding="utf-8").splitlines() if line.strip()]
    configs = meta["configs"]
    pass_sets = []
    for i in range(meta["n_configs"]):
        hdr = raw[i * width:(i + 1) * width]
        bits = {j for j in range(n) if (hdr[j // 8] >> (j % 8)) & 1}
        pass_sets.append(bits)
    return meta, configs, tasks, pass_sets


def pct(k, n):
    return round(100.0 * k / n, 1)


def main():
    meta, configs, tasks, pass_sets = load()
    n = meta["n_tasks"]
    names = [c["config_name"] for c in configs]
    base_i = names.index(BASELINE)
    base = pass_sets[base_i]
    all_union = set().union(*pass_sets)

    rows = []
    for i, c in enumerate(configs):
        s = pass_sets[i]
        unique_all = s - set().union(*(pass_sets[j] for j in range(len(pass_sets)) if j != i))
        lost = base - s
        gained = s - base
        net = len(gained) - len(lost)
        if i == base_i:
            flag = "baseline"
        elif len(lost) >= 5 and net < 0:
            flag = "severe_regression"
        elif len(lost) > len(gained):
            flag = "regression"
        elif len(lost) == len(gained):
            flag = "neutral"
        else:
            flag = "improvement"
        best = None
        for j in range(len(pass_sets)):
            if j == i:
                continue
            u = s | pass_sets[j]
            comp = len(u) - max(len(s), len(pass_sets[j]))
            jac = len(s & pass_sets[j]) / len(u) if u else 0.0
            cand = (len(u), comp, -j, j, len(s & pass_sets[j]), jac)
            if best is None or cand > best:
                best = cand
        union, comp, _, partner, inter, jac = best
        rows.append({
            "config_name": c["config_name"],
            "config_key": c["config_key"],
            "full_sha256": c["full_sha256"],
            "size_mb": c["size_mb"],
            "pass_count": len(s),
            "pass_rate": round(len(s) / n, 6),
            "pass_pct": pct(len(s), n),
            "unique_tasks_all": len(unique_all),
            "gained_vs_baseline": len(gained),
            "lost_vs_baseline": len(lost),
            "net_vs_baseline": net,
            "regression_flag": flag,
            "best_partner": names[partner],
            "best_partner_union": union,
            "best_partner_union_pct": pct(union, n),
            "best_partner_complementarity": comp,
            "best_partner_jaccard": round(jac, 4),
        })

    pairs = []
    for i, j in combinations(range(len(names)), 2):
        a, b = pass_sets[i], pass_sets[j]
        u = a | b
        inter = a & b
        pairs.append({
            "pair_a": names[i],
            "pair_b": names[j],
            "union": len(u),
            "union_pct": pct(len(u), n),
            "intersection": len(inter),
            "jaccard": round(len(inter) / len(u), 4) if u else 0.0,
            "complementarity": len(u) - max(len(a), len(b)),
            "unique_a": len(a - b),
            "unique_b": len(b - a),
        })
    pairs.sort(key=lambda r: (-r["union"], -r["complementarity"], r["pair_a"], r["pair_b"]))

    cert = json.loads(CERTS.read_text(encoding="utf-8"))
    claim_map = json.loads(CLAIMS.read_text(encoding="utf-8"))
    status_counts = Counter(c["status"] for c in claim_map["claims"])
    rule = cert["rule_certificate"]
    task_cert = cert["task_certificate"]["heldout"]

    # Example insight: the best pair's gain over the baseline is the complement's
    # off-baseline passes, not its total pass count.
    top = pairs[0]
    pair_names = [top["pair_a"], top["pair_b"]]
    if BASELINE in pair_names:
        other = pair_names[0] if pair_names[1] == BASELINE else pair_names[1]
        other_i = names.index(other)
        off_base = len(pass_sets[other_i] - base)
        insight = (
            f"Best pair {top['pair_a']} + {top['pair_b']} reaches {top['union']}/{n} "
            f"({top['union_pct']}%), {top['complementarity']} tasks above the best single. "
            f"The complement {other} passes {len(pass_sets[other_i])}/{n}, but only "
            f"{off_base} of those passes are outside the baseline; the pair gain is "
            f"{off_base}, not the complement's total pass count."
        )
    else:
        insight = (
            f"Best pair {top['pair_a']} + {top['pair_b']} reaches {top['union']}/{n} "
            f"({top['union_pct']}%), {top['complementarity']} tasks above the best single."
        )

    out = {
        "scope": "14 Qwen configs x 60 HumanEval heldout tasks; exact pass-set headers",
        "source": str(META),
        "task_list_sha256_newline": meta["task_list_sha256_newline"],
        "matrix_sha256_canonical": meta["matrix_sha256_canonical"],
        "baseline": BASELINE,
        "n_configs": len(names),
        "n_tasks": n,
        "oracle_union": len(all_union),
        "oracle_union_pct": pct(len(all_union), n),
        "configs": rows,
        "pairs": pairs,
        "pairs_top20": pairs[:20],
        "certificate_summary": {
            "rule_id": rule["id"],
            "rule_decision": rule["decision"],
            "claim_counts": dict(status_counts),
            "no_orphan_claims": claim_map["no_orphan_claims"],
            "orphan_claims": claim_map["orphan_claims"],
            "heldout_task_list_sha256_newline": task_cert["task_list_sha256_newline"],
        },
        "example_insight": insight,
    }
    (HERE / "report_card.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    # Markdown report.
    lines = []
    lines.append("# Behavioral report card — 14 Qwen configs")
    lines.append("")
    lines.append("**Scope:** 14 Qwen2.5-Coder-1.5B configurations x 60 HumanEval heldout tasks. "
                 "Exact pass-set headers from the repository-backed evidence manifest; no new run.")
    lines.append("")
    lines.append(f"**Baseline:** `{BASELINE}` ({len(base)}/{n} = {pct(len(base), n)}%). "
                 f"**Oracle union:** {len(all_union)}/{n} = {pct(len(all_union), n)}%.")
    lines.append("")
    lines.append("**Regression flags:** `severe_regression` = lost >=5 baseline passes and net <0; "
                 "`regression` = lost > gained; `neutral` = lost == gained; `improvement` = gained > lost.")
    lines.append("")
    lines.append("## 1. Per-config report card")
    lines.append("")
    lines.append("| Config | MiB | Pass | Rate | Unique | + vs base | - vs base | Net | Flag | Best partner | Union | Compl. |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|")
    for r in sorted(rows, key=lambda x: (-x["pass_count"], x["config_name"])):
        lines.append(
            f"| `{r['config_name']}` | {r['size_mb']:.2f} | {r['pass_count']}/{n} | "
            f"{r['pass_pct']}% | {r['unique_tasks_all']} | {r['gained_vs_baseline']} | "
            f"{r['lost_vs_baseline']} | {r['net_vs_baseline']:+d} | {r['regression_flag']} | "
            f"`{r['best_partner']}` | {r['best_partner_union']}/{n} | "
            f"{r['best_partner_complementarity']} |"
        )
    lines.append("")
    lines.append("## 2. Pairwise complementarity — top 10")
    lines.append("")
    lines.append("| Pair | Union | Union % | Complementarity | Jaccard | Unique A | Unique B |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for p in pairs[:10]:
        lines.append(
            f"| `{p['pair_a']}` + `{p['pair_b']}` | {p['union']}/{n} | {p['union_pct']}% | "
            f"{p['complementarity']} | {p['jaccard']:.3f} | {p['unique_a']} | {p['unique_b']} |"
        )
    lines.append("")
    lines.append("## 3. Regression audit")
    lines.append("")
    reg = [r for r in rows if r["regression_flag"] in ("regression", "severe_regression")]
    if reg:
        lines.append("| Config | Lost vs baseline | Gained vs baseline | Net | Flag |")
        lines.append("|---|---:|---:|---:|---|")
        for r in sorted(reg, key=lambda x: (-x["lost_vs_baseline"], x["config_name"])):
            lines.append(f"| `{r['config_name']}` | {r['lost_vs_baseline']} | {r['gained_vs_baseline']} | {r['net_vs_baseline']:+d} | {r['regression_flag']} |")
    else:
        lines.append("No config loses more baseline passes than it gains.")
    lines.append("")
    lines.append("## 4. Certificate summary")
    lines.append("")
    lines.append(f"- Rule certificate `{rule['id']}`: **{rule['decision']}**.")
    lines.append(f"- Claims: {dict(status_counts)}; orphan claims: {claim_map['orphan_claims']}.")
    lines.append(f"- Heldout task-list SHA-256: `{task_cert['task_list_sha256_newline']}`.")
    lines.append("")
    lines.append("## 5. Example insight")
    lines.append("")
    lines.append(insight)
    lines.append("")
    lines.append("## 6. Reproduce")
    lines.append("")
    lines.append("```")
    lines.append("python harness/architect/queue/report-card-demo/report_card.py")
    lines.append("```")
    lines.append("")
    (HERE / "REPORT_CARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {HERE / 'report_card.json'}")
    print(f"wrote {HERE / 'REPORT_CARD.md'}")
    print("insight:", insight)


if __name__ == "__main__":
    main()



#!/usr/bin/env python3
"""Score a Kaggle inference results.json on the local frozen repos.

Usage:
    python score_kaggle_results.py --results path/to/results.json --tag 14b
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Anton\.lmstudio\apps\bionic\projects\d49037d8-47f4-5808-9028-c707de117f8f\workspace\LLM intagration")
import sys as _sys
_sys.path.insert(0, str(ROOT / "gemma4_paper_track_48h" / "artifacts" / "search_replace"))
from edit_contract import DirTree, apply_reply
WORK = ROOT / "harness" / "architect" / "queue" / "repo_comp_40" / "work"
BASE = ROOT / "gemma4_paper_track_48h" / "artifacts"
LOGS = BASE / "kaggle_scoring_logs"


def sh(args, cwd=None, timeout=120):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def load_data():
    from datasets import load_dataset
    return {r["instance_id"]: r for r in load_dataset("princeton-nlp/SWE-bench_Lite", split="test")}


def clean_reply_unused(reply: str) -> str:
    text = (reply or "").replace("\r\n", "\n").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:diff)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    lines = [line for line in text.splitlines() if not line.startswith("index ")]
    return "\n".join(lines).strip()


def gold_paths(task):
    return [b for _, b in re.findall(r"^diff --git a/(\S+) b/(\S+)", task.get("patch", ""), re.M)]


def reply_paths(reply):
    return [b for _, b in re.findall(r"^diff --git a/(\S+) b/(\S+)", reply, re.M)]


def run_tests(repo, task, tag, iid):
    if task["repo"] != "django/django":
        return {"test": "not-run", "reason": "environment-limited"}
    modules = set()
    f2p = task.get("FAIL_TO_PASS", [])
    if isinstance(f2p, str):
        try:
            f2p = json.loads(f2p)
        except json.JSONDecodeError:
            f2p = []
    for name in f2p:
        m = re.search(r"\(([^)]+)\)", name)
        if m:
            parts = m.group(1).split(".")
            if len(parts) >= 2:
                modules.add(".".join(parts[:2]))
    if not modules:
        return {"test": "not-run", "reason": "no-module"}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    r = sh([sys.executable, "tests/runtests.py", "--verbosity", "1", "--parallel", "1", *sorted(modules)], cwd=repo, timeout=300)
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"{tag}_{iid}.log"
    log.write_text((r.stdout or "") + "\n" + (r.stderr or ""), encoding="utf-8")
    return {"test": "pass" if r.returncode == 0 else "fail", "rc": r.returncode, "log": str(log.relative_to(ROOT))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()

    payload = json.loads(Path(args.results).read_text(encoding="utf-8"))
    data = load_data()
    rows = []
    for task_row in payload.get("tasks", []):
        iid = task_row.get("instance_id")
        if iid not in data:
            continue
        task = data[iid]
        repo = WORK / iid
        raw = task_row.get("reply") or ""
        reply = clean_reply_unused(raw)
        row = {"instance_id": iid, "gold_file": task_row.get("gold_file"), "reply_bytes": len(reply), "sr_ok": False, "sr_issues": []}
        try:
            sh(["git", "-C", str(repo), "config", "core.autocrlf", "false"])
            sh(["git", "-C", str(repo), "checkout", "--force", task["base_commit"]])
            sh(["git", "-C", str(repo), "clean", "-fdq", "-e", "reply_*.diff", "-e", "test_patch.diff"])
            tp = repo / "test_patch.diff"
            tp.write_text(task["test_patch"].replace("\r\n", "\n"), encoding="utf-8", newline="\n")
            sh(["git", "-C", str(repo), "apply", "--whitespace=nowarn", str(tp)])
            mp = repo / f"kaggle_{args.tag}.diff"
            mp.write_text(reply + "\n", encoding="utf-8", newline="\n")
            strict = sh(["git", "-C", str(repo), "apply", "--check", "--whitespace=nowarn", str(mp)])
            lenient = sh(["git", "-C", str(repo), "apply", "--check", "--recount", "--whitespace=nowarn", str(mp)])
            row["strict"] = strict.returncode == 0
            row["lenient"] = lenient.returncode == 0
            row["apply_error"] = (strict.stderr or "")[:500]
            row["gold_hit"] = any(g in reply_paths(reply) for g in gold_paths(task))
            if row["strict"] or row["lenient"]:
                apply_flag = "--recount" if not row["strict"] else "--whitespace=nowarn"
                sh(["git", "-C", str(repo), "apply", apply_flag, str(mp)])
                row["tests"] = run_tests(repo, task, args.tag, iid)
            else:
                row["tests"] = {"test": "not-run", "reason": "patch-not-applied"}
        except Exception as exc:  # noqa: BLE001
            row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
        print(json.dumps(row)[:400], flush=True)

    out = BASE / f"kaggle_audit_{args.tag}.json"
    out.write_text(json.dumps({"tag": args.tag, "results": args.results, "rows": rows}, indent=2), encoding="utf-8")
    print("strict", sum(r.get("strict") for r in rows), "lenient", sum(r.get("lenient") for r in rows), "gold", sum(r.get("gold_hit") for r in rows), "out", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

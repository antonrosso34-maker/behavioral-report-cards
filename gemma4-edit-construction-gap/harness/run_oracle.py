#!/usr/bin/env python3
"""Oracle-file arm: give Gemma 4 the exact gold file, not the gold patch.

8 tasks from the frozen split. One generation + one apply-error repair.
Measures whether the model can construct an applicable/correct edit when
localization is removed as a variable.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Users\Anton\.lmstudio\apps\bionic\projects\d49037d8-47f4-5808-9028-c707de117f8f\workspace\LLM intagration")
WORK = ROOT / "harness" / "architect" / "queue" / "repo_comp_40" / "work"
OUT = ROOT / "gemma4_paper_track_48h" / "artifacts" / "oracle_hunk_replies"
RESULTS = ROOT / "gemma4_paper_track_48h" / "artifacts" / "oracle_hunk_results.json"
SERVER = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "gemma-4-E2B-it-qat-UD-Q4_K_XL"
TASKS = [
    "django__django-16816",
    "django__django-12589",
    "astropy__astropy-12907",
    "matplotlib__matplotlib-23913",
    "matplotlib__matplotlib-23563",
    "matplotlib__matplotlib-25433",
    "mwaskom__seaborn-3407",
    "pallets__flask-4045",
]


def sh(args, cwd=None, timeout=120):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def load_data():
    from datasets import load_dataset
    return {r["instance_id"]: r for r in load_dataset("princeton-nlp/SWE-bench_Lite", split="test")}


def gold_file(task):
    m = re.search(r"^diff --git a/(\S+) b/(\S+)", task["patch"], re.M)
    if not m:
        raise ValueError("no gold file")
    return m.group(2)


def excerpt(path: Path, task) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if len(lines) <= 600:
        return text
    hunks = []
    for match in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", task["patch"], re.M):
        start = int(match.group(1)) - 1
        count = int(match.group(2)) if match.group(2) else 1
        hunks.append((max(0, start - 40), min(len(lines), start + count + 40)))
    if not hunks:
        return "\n".join(lines[:300])
    hunks.sort()
    merged = []
    for start, end in hunks:
        if merged and start <= merged[-1][1] + 20:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return "\n\n".join(f"[WINDOW lines {s + 1}-{e}]\n" + "\n".join(lines[s:e]) for s, e in merged)


def ask(prompt: str) -> tuple[str, dict]:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1600,
        "temperature": 0,
        "stream": False,
    }).encode()
    req = urllib.request.Request(SERVER, data=body, headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=900) as resp:
        payload = json.loads(resp.read())
    elapsed = time.perf_counter() - started
    choice = payload["choices"][0]
    return choice["message"]["content"], {"latency_s": round(elapsed, 3), "usage": payload.get("usage", {}), "finish_reason": choice.get("finish_reason")}


def prompt_for(task, path, content):
    return (
        f"Repository: {task['repo']}\n"
        f"Issue:\n{task['problem_statement'][:4000]}\n\n"
        f"Target file: {path}\n"
        f"Current content of {path}:\n```python\n{content}\n```\n\n"
        f"Return a unified diff patch only. Start with 'diff --git a/{path} b/{path}'. "
        "Use exact context from the file. Do not modify tests. Do not use markdown fences. Do not explain."
    )


def repair_prompt(task, path, content, previous, error):
    return prompt_for(task, path, content) + (
        f"\n\nYour previous patch failed to apply with this error:\n{error[:800]}\n\n"
        f"Previous patch:\n{previous[:3000]}\n\n"
        "Return a corrected unified diff only. Use exact paths and exact context."
    )


def check(repo, reply):
    p = repo / "oracle_tmp.diff"
    text = reply.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:diff)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    p.write_text(text + "\n", encoding="utf-8", newline="\n")
    strict = sh(["git", "-C", str(repo), "apply", "--check", "--whitespace=nowarn", str(p)])
    lenient = sh(["git", "-C", str(repo), "apply", "--check", "--recount", "--whitespace=nowarn", str(p)])
    return strict.returncode == 0, lenient.returncode == 0, (strict.stderr or "")[:800], text


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = load_data()
    results = {"model": MODEL, "arm": "oracle-file", "tasks": []}
    for iid in TASKS:
        task = data[iid]
        repo = WORK / iid
        row = {"instance_id": iid, "repo": task["repo"]}
        try:
            sh(["git", "-C", str(repo), "config", "core.autocrlf", "false"])
            sh(["git", "-C", str(repo), "checkout", "--force", task["base_commit"]])
            sh(["git", "-C", str(repo), "clean", "-fdq", "-e", "reply_*.diff", "-e", "test_patch.diff"])
            path = gold_file(task)
            content = excerpt(repo / path, task)
            prompt = prompt_for(task, path, content)
            reply, meta = ask(prompt)
            strict, lenient, err, clean = check(repo, reply)
            row.update(meta)
            row.update({"gold_file": path, "strict": strict, "lenient": lenient, "first_error": err, "prompt_chars": len(prompt)})
            if not strict:
                reply2, meta2 = ask(repair_prompt(task, path, content, clean, err))
                strict2, lenient2, err2, clean2 = check(repo, reply2)
                row.update({"repair_strict": strict2, "repair_lenient": lenient2, "repair_error": err2, "repair_latency_s": meta2["latency_s"], "repair_usage": meta2["usage"]})
                reply = reply2
            (OUT / f"{iid}.diff").write_text(reply, encoding="utf-8", newline="\n")
            row["reply_bytes"] = len(reply)
            row["has_diff"] = "diff --git" in reply
        except Exception as exc:  # noqa: BLE001
            row["error"] = f"{type(exc).__name__}: {exc}"
        results["tasks"].append(row)
        print(json.dumps(row)[:500], flush=True)
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Gemma 4 E2B retrieval-augmented patch screen on the frozen 20-task split.

Arm: issue -> keyword retrieval over the repository -> top-k exact file excerpts ->
unified diff -> git apply --check -> optional one repair turn fed by the apply error.
No hidden tests are read. Test files are excluded from retrieval.
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
SPLIT = ROOT / "harness" / "architect" / "queue" / "repo_comp_40" / "split_20.json"
WORK = ROOT / "harness" / "architect" / "queue" / "repo_comp_40" / "work"
OUT = ROOT / "gemma4_paper_track_48h" / "artifacts" / "gemma4_retrieval_replies"
RESULTS = ROOT / "gemma4_paper_track_48h" / "artifacts" / "gemma4_retrieval_results.json"
SERVER = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "gemma-4-E2B-it-qat-UD-Q4_K_XL"

SKIP_DIRS = {".git", ".venv", ".venv-train", "node_modules", "__pycache__", ".ruff_cache", "build", "dist", ".tox", ".eggs"}
TEXT_SUFFIXES = {".py", ".md", ".rst", ".txt", ".toml", ".cfg", ".ini", ".yaml", ".yml"}
STOP = set("the a an and or of to in for on with is are was were be been being this that these those it its as at by from we you they i he she them our your their not no yes if then else when where which who whom whose what how why can could should would may might must will shall do does did done have has had".split())


def sh(args: list[str], cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def load_data():
    from datasets import load_dataset
    return {r["instance_id"]: r for r in load_dataset("princeton-nlp/SWE-bench_Lite", split="test")}


def reset(task: dict) -> Path:
    repo = WORK / task["instance_id"]
    sh(["git", "-C", str(repo), "config", "core.autocrlf", "false"])
    sh(["git", "-C", str(repo), "checkout", "--force", task["base_commit"]])
    sh(["git", "-C", str(repo), "clean", "-fdq", "-e", "reply_*.diff", "-e", "test_patch.diff"])
    return repo


def terms(text: str) -> list[str]:
    toks = [t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", text)]
    out = []
    for t in toks:
        if t in STOP or len(t) > 40:
            continue
        if t not in out:
            out.append(t)
    return out[:40]


def candidate_files(repo: Path) -> list[Path]:
    files = []
    for root, dirs, names in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in names:
            p = Path(root) / name
            if p.suffix.lower() != ".py":
                continue
            rel = str(p.relative_to(repo)).replace("\\", "/")
            low = rel.lower()
            if low.startswith(("tests/", "docs/", "doc/", "cextern/", "build/", "dist/", "benchmarks/")):
                continue
            if "/tests/" in low or "/test_" in low or low.endswith("_test.py"):
                continue
            try:
                if p.stat().st_size > 300_000:
                    continue
            except OSError:
                continue
            files.append(p)
    return files


def retrieve(repo: Path, query: list[str], k: int = 3) -> list[tuple[Path, str, int, str]]:
    scored = []
    for p in candidate_files(repo):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        low = text.lower()
        score = sum(low.count(q) for q in query)
        if score <= 0:
            continue
        rel = str(p.relative_to(repo)).replace("\\", "/").lower()
        stem = p.stem.lower()
        score += 5
        if any(q in stem for q in query):
            score += 12
        if "/src/" in rel or rel.startswith("src/"):
            score += 5
        if "test" in stem:
            score -= 20
        scored.append((score, p, text))
    scored.sort(key=lambda x: (-x[0], len(x[2])))
    out = []
    for score, p, text in scored[:k]:
        rel = str(p.relative_to(repo)).replace("\\", "/")
        lines = text.splitlines()
        first = 0
        for i, line in enumerate(lines):
            if any(q in line.lower() for q in query):
                first = max(0, i - 25)
                break
        excerpt = "\n".join(lines[first:first + 80])
        out.append((p, rel, score, excerpt[:2600]))
    return out


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
    return choice["message"]["content"], {
        "latency_s": round(elapsed, 3),
        "finish_reason": choice.get("finish_reason"),
        "usage": payload.get("usage", {}),
    }


def prompt_for(task: dict, files: list[tuple[Path, str, int, str]]) -> str:
    parts = [
        f"Repository: {task['repo']}",
        "Issue:",
        task["problem_statement"][:3000],
        "",
        f"Public tests: {task['PASS_TO_PASS'][:8]}",
        "",
        "Candidate files (exact repository-relative paths and excerpts):",
    ]
    for _, rel, _, excerpt in files:
        parts.append(f"\nFILE: {rel}\n```python\n{excerpt[:2600]}\n```")
    parts.append(
        "\nReturn a unified diff patch only. Start with 'diff --git'. "
        "Use the exact paths above. Do not modify tests. Do not use markdown fences. Do not explain."
    )
    return "\n".join(parts)


def repair_prompt(task: dict, files, previous: str, error: str) -> str:
    return (
        prompt_for(task, files)
        + "\n\nYour previous patch failed to apply with this error:\n"
        + error[:1000]
        + "\n\nPrevious patch:\n"
        + previous[:4000]
        + "\n\nReturn a corrected unified diff only. Use exact paths and exact context."
    )


def apply_check(repo: Path, reply: str) -> tuple[bool, str]:
    p = repo / "gemma_reply.diff"
    text = reply.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:diff)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    p.write_text(text + "\n", encoding="utf-8", newline="\n")
    r = sh(["git", "-C", str(repo), "apply", "--check", "--recount", "--whitespace=nowarn", str(p)])
    return r.returncode == 0, (r.stderr or r.stdout or "")[:1000]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    data = load_data()
    results = {"model": MODEL, "arm": "retrieval+repair", "tasks": []}
    for stage in ("discovery", "confirmation"):
        for item in split[stage]:
            iid = item["instance_id"]
            task = data[iid]
            row = {"instance_id": iid, "repo": task["repo"], "stage": stage}
            try:
                repo = reset(task)
                q = terms(task["problem_statement"])
                files = retrieve(repo, q, k=3)
                row["retrieved"] = [rel for _, rel, _, _ in files]
                prompt = prompt_for(task, files)
                reply, meta = ask(prompt)
                ok, err = apply_check(repo, reply)
                row.update(meta)
                row["first_apply"] = ok
                row["first_error"] = "" if ok else err
                if not ok:
                    reply2, meta2 = ask(repair_prompt(task, files, reply, err))
                    ok2, err2 = apply_check(repo, reply2)
                    row["repair_apply"] = ok2
                    row["repair_error"] = "" if ok2 else err2
                    row["repair_latency_s"] = meta2["latency_s"]
                    row["repair_usage"] = meta2["usage"]
                    reply = reply2
                path = OUT / f"{iid}.diff"
                path.write_text(reply, encoding="utf-8", newline="\n")
                row["reply_bytes"] = len(reply)
                row["has_diff"] = "diff --git" in reply
                row["reply_path"] = str(path.relative_to(ROOT))
                row["prompt_chars"] = len(prompt)
            except Exception as exc:  # noqa: BLE001
                row["error"] = f"{type(exc).__name__}: {exc}"
            results["tasks"].append(row)
            print(json.dumps(row)[:500], flush=True)
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    import os
    sys.exit(main())

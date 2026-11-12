#!/usr/bin/env python3
"""Gemma 4 E2B single-shot SWE-bench Lite screen on the frozen 20-task split.

Same prompt shape as the existing REPO-COMP-40 screen, so the result is comparable
to the saved q3km_code / mx_q4km attempts. Saves one reply per task; no test execution.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Users\Anton\.lmstudio\apps\bionic\projects\d49037d8-47f4-5808-9028-c707de117f8f\workspace\LLM intagration")
SPLIT = ROOT / "harness" / "architect" / "queue" / "repo_comp_40" / "split_20.json"
WORK = ROOT / "harness" / "architect" / "queue" / "repo_comp_40" / "work"
OUT = ROOT / "gemma4_paper_track_48h" / "artifacts" / "gemma4_replies"
RESULTS = ROOT / "gemma4_paper_track_48h" / "artifacts" / "gemma4_results.json"
SERVER = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "gemma-4-E2B-it-qat-UD-Q4_K_XL"


def sh(args: list[str], cwd: Path | None = None, timeout: int = 1200) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def load_data():
    from datasets import load_dataset
    return {r["instance_id"]: r for r in load_dataset("princeton-nlp/SWE-bench_Lite", split="test")}


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


def prepare(task: dict) -> Path:
    repo = WORK / task["instance_id"]
    if not repo.exists():
        raise FileNotFoundError(repo)
    sh(["git", "-C", str(repo), "config", "core.autocrlf", "false"])
    sh(["git", "-C", str(repo), "checkout", "--force", task["base_commit"]])
    sh(["git", "-C", str(repo), "clean", "-fdq", "-e", "reply_*.diff", "-e", "test_patch.diff"])
    tp = repo / "test_patch.diff"
    if not tp.exists():
        tp.write_text(task["test_patch"], encoding="utf-8", newline="\n")
    else:
        text = tp.read_text(encoding="utf-8").replace("\r\n", "\n")
        tp.write_text(text, encoding="utf-8", newline="\n")
    sh(["git", "-C", str(repo), "apply", "--whitespace=nowarn", str(tp)])
    return repo


def prompt_for(task: dict) -> str:
    return (
        f"Repository: {task['repo']}\n"
        f"Issue:\n{task['problem_statement']}\n\n"
        f"Public tests: {task['PASS_TO_PASS'][:8]}\n\n"
        "Return a unified diff patch only. Start with 'diff --git'. "
        "Use exact repository-relative paths and exact context lines from the repository. "
        "Do not use markdown fences. Do not modify tests. Do not explain."
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    data = load_data()
    results = {"model": MODEL, "prompt": "single-shot-v1", "tasks": []}
    for stage in ("discovery", "confirmation"):
        for item in split[stage]:
            iid = item["instance_id"]
            task = data[iid]
            row = {"instance_id": iid, "repo": task["repo"], "stage": stage}
            try:
                prepare(task)
                prompt = prompt_for(task)
                reply, meta = ask(prompt)
                path = OUT / f"{iid}.diff"
                path.write_text(reply, encoding="utf-8", newline="\n")
                row.update(meta)
                row["reply_bytes"] = len(reply)
                row["has_diff"] = "diff --git" in reply
                row["reply_path"] = str(path.relative_to(ROOT))
                row["prompt_chars"] = len(prompt)
            except Exception as exc:  # noqa: BLE001
                row["error"] = f"{type(exc).__name__}: {exc}"
            results["tasks"].append(row)
            print(json.dumps(row)[:400], flush=True)
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

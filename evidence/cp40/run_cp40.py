#!/usr/bin/env python3
"""Run one arm of the frozen 40-task CP@1 panel (analysis run; do not launch here).

The lead launches this through run_cp40_lowprio.ps1 under the eval lock and at
below-normal priority. The script itself does not acquire the lock.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # .../harness
sys.path.insert(0, str(ROOT / "scripts"))

from common import (  # noqa: E402
    DEFAULT_CONTEXT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_THREADS,
    SERVER_LOG_DIR,
    chat,
    compose_solution,
    file_size_mb,
    load_dataset,
    read_jsonl,
    sandbox_run,
    server_cpu_seconds,
    server_rss_mb,
    sha256_file,
    start_server,
    stop_server,
    summarize_task_rows,
    task_messages,
    wait_health,
    write_json,
)

EXPECTED_SHA = {
    "anchor": "fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb",
    "complement": "f03ecc3eeb5f957f1331aae886779730bbaa9f1825d1abd075fa894407760b74",
}


def set_below_normal(pid: int) -> None:
    if os.name != "nt":
        return
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Process -Id {pid}).PriorityClass = 'BelowNormal'"],
            check=False, capture_output=True, text=True,
        )
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split-json", default=str(HERE / "cp40_split.json"))
    parser.add_argument("--arm", choices=["anchor", "complement"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--label")
    parser.add_argument("--backend", choices=["cpu", "vulkan"], default="cpu")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    parser.add_argument("--context", type=int, default=DEFAULT_CONTEXT)
    parser.add_argument("--kv-cache", choices=["f16", "q8_0", "q4_0"], required=True)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--request-timeout", type=float, default=600.0)
    parser.add_argument("--test-timeout", type=float, default=30.0)
    parser.add_argument("--port", type=int, default=8140)
    parser.add_argument("--output")
    parser.add_argument("--priority", choices=["below-normal", "normal"], default="below-normal")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    split = json.loads(Path(args.split_json).read_text(encoding="utf-8"))
    tasks = split["tasks"]
    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"model not found: {model_path}")
    actual_sha = sha256_file(model_path)
    expected_sha = EXPECTED_SHA[args.arm]
    if actual_sha != expected_sha:
        raise SystemExit(f"model SHA mismatch for {args.arm}: {actual_sha} != {expected_sha}")

    label = args.label or f"cp40_{args.arm}"
    output = Path(args.output) if args.output else ROOT / "results" / "cp40" / f"{label}.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(output) if args.resume else []
    if not args.resume:
        output.write_text("", encoding="utf-8")
    done = {row["task_id"] for row in rows}
    pending = [t for t in tasks if t["task_id"] not in done]
    if not pending:
        print("all panel tasks already present")
        return

    if args.priority == "below-normal":
        set_below_normal(os.getpid())

    datasets = {"humaneval": load_dataset("humaneval"), "mbpp": load_dataset("mbpp")}
    for t in pending:
        if t["task_id"] not in datasets[t["dataset"]]:
            raise SystemExit(f"task missing from dataset: {t}")

    base_url = f"http://127.0.0.1:{args.port}"
    log_path = SERVER_LOG_DIR / f"{label}_cp40_{args.port}.log"
    process = start_server(
        model_path,
        backend=args.backend,
        threads=args.threads,
        context=args.context,
        port=args.port,
        kv_cache=args.kv_cache,
        log_path=log_path,
    )
    if args.priority == "below-normal":
        set_below_normal(process.pid)
    try:
        wait_health(base_url, process, timeout=900)
        print(f"server ready; pending {len(pending)} tasks; priority={args.priority}")
        for index, t in enumerate(pending, start=1):
            problem = datasets[t["dataset"]][t["task_id"]]
            messages = task_messages(t["dataset"], problem)
            cpu_before = server_cpu_seconds(process)
            started = time.perf_counter()
            status = "ok"
            detail = ""
            completion = ""
            usage = {}
            finish_reason = None
            try:
                reply = chat(
                    base_url, messages,
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                    timeout=args.request_timeout,
                )
                completion = reply["content"]
                usage = reply["usage"]
                finish_reason = reply["finish_reason"]
            except Exception as error:
                status = "request_error"
                detail = str(error)
            wall_seconds = time.perf_counter() - started
            cpu_seconds = max(0.0, server_cpu_seconds(process) - cpu_before)
            passed = False
            sandbox = {"status": "not_run", "detail": "", "seconds": None}
            if status == "ok":
                program = compose_solution(t["dataset"], problem, completion)
                if program is None:
                    status = "no_function"
                    detail = "could not extract a callable function"
                else:
                    sandbox = sandbox_run(program, timeout=args.test_timeout)
                    status = sandbox["status"]
                    detail = sandbox["detail"]
                    passed = bool(sandbox["passed"])
            row = {
                "task_id": t["task_id"],
                "dataset": t["dataset"],
                "source_split": t["split"],
                "split": "cp40",
                "entry_point": problem["entry_point"],
                "arm": args.arm,
                "label": label,
                "status": status,
                "passed": passed,
                "detail": detail,
                "completion": completion,
                "usage": usage,
                "finish_reason": finish_reason,
                "hit_token_limit": finish_reason == "length" or int(usage.get("completion_tokens") or 0) >= args.max_tokens,
                "max_tokens": args.max_tokens,
                "seconds": round(wall_seconds, 4),
                "cpu_seconds": round(cpu_seconds, 4),
                "sandbox_seconds": sandbox.get("seconds"),
                "plus_checked": sandbox.get("plus_checked"),
                "plus_skipped": sandbox.get("plus_skipped"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "timestamp": datetime.now(UTC).isoformat(),
            }
            with output.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows.append(row)
            print(f"{index:>2}/{len(pending)} {'pass' if passed else 'FAIL'} {t['dataset']}/{t['task_id']}")
    finally:
        stop_server(process)

    summary = {
        "label": label,
        "arm": args.arm,
        "model": str(model_path),
        "model_sha256": actual_sha,
        "model_size_mb": file_size_mb(model_path),
        "split_json": str(args.split_json),
        "panel_sha256": split["hashes"]["panel_40_sha256_newline"],
        "backend": args.backend,
        "threads": args.threads,
        "context": args.context,
        "kv_cache": args.kv_cache,
        "priority": args.priority,
        "finished_at": datetime.now(UTC).isoformat(),
    }
    summary.update(summarize_task_rows(rows))
    write_json(output.with_name(output.stem + "_summary.json"), summary)
    print(f"wrote {output} and summary")


if __name__ == "__main__":
    main()

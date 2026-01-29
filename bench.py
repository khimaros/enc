#!/usr/bin/env python3
"""benchmark runner for enc transpilation."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

BENCHMARKS_DIR = "benchmarks"
RESULTS_FILE = "results.json"
LOGS_DIR = "logs"


def parse_args():
    parser = argparse.ArgumentParser(description="run enc transpilation benchmarks")
    parser.add_argument("language", help="target language (e.g., rust, python)")
    parser.add_argument("iterations", type=int, help="number of iterations per model")
    parser.add_argument(
        "models",
        nargs="+",
        help="provider/model pairs (e.g., google/gemini-3-flash-preview)",
    )
    return parser.parse_args()


def load_existing_results(path):
    """load existing benchmark results or return empty structure."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"benchmarks": []}


def save_results(path, data):
    """save benchmark results to json file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_or_create_language_entry(data, language):
    """find existing language entry or create a new one."""
    for entry in data["benchmarks"]:
        if entry["target_language"] == language:
            return entry
    entry = {"target_language": language, "results": []}
    data["benchmarks"].append(entry)
    return entry


def get_next_run_number(results, provider, model):
    """determine next run number for a provider/model combo."""
    existing = [
        r["run"] for r in results if r["provider"] == provider and r["model"] == model
    ]
    return max(existing, default=0) + 1


def parse_tokens(token_str):
    """parse token string into structured dict."""
    tokens = {"input": 0, "output": 0, "thinking": None}
    if not token_str or token_str == "N/A":
        return tokens

    input_match = re.search(r"(\d+)\s*input", token_str)
    output_match = re.search(r"(\d+)\s*output", token_str)
    thinking_match = re.search(r"(\d+)\s*thinking", token_str)

    if input_match:
        tokens["input"] = int(input_match.group(1))
    if output_match:
        tokens["output"] = int(output_match.group(1))
    if thinking_match:
        tokens["thinking"] = int(thinking_match.group(1))

    return tokens


def parse_cost(cost_str):
    """parse cost string like '$1.234' into float."""
    if not cost_str or cost_str == "N/A":
        return 0.0
    return float(cost_str.replace("$", ""))


def parse_time(time_str):
    """parse time string like '123.45s' into float seconds."""
    if not time_str or time_str == "N/A":
        return 0.0
    return float(time_str.replace("s", ""))


def setup_benchmark_dir(tmp_dir, root_dir, language):
    """copy necessary files to benchmark directory."""
    tmp = Path(tmp_dir)
    root = Path(root_dir)

    (tmp / "src").mkdir(parents=True, exist_ok=True)
    (tmp / "testdata").mkdir(parents=True, exist_ok=True)

    files_to_copy = [
        ("src/enc.en", "src/enc.en"),
        (".enc.env.example", ".enc.env.example"),
        ("Makefile", "Makefile"),
        ("CMakeLists.txt", "CMakeLists.txt"),
        ("Cargo.toml", "Cargo.toml"),
        ("requirements.txt", "requirements.txt"),
        ("package.json", "package.json"),
        (".enc.env", ".enc.env"),
        ("test.sh", "test.sh"),
    ]

    for src, dst in files_to_copy:
        src_path = root / src
        if src_path.exists():
            shutil.copy2(src_path, tmp / dst)

    dirs_to_copy = [
        ("res", "res"),
        ("testdata/goldens", "testdata/goldens"),
        ("tests", "tests"),
    ]

    for src, dst in dirs_to_copy:
        src_path = root / src
        if src_path.exists():
            if (tmp / dst).exists():
                shutil.rmtree(tmp / dst)
            shutil.copytree(src_path, tmp / dst)

    # copy enc files preserving type (symlink or regular file)
    enc_files_to_copy = ["enc", "enc-release", f"enc-{language}"]
    for name in enc_files_to_copy:
        src_path = root / name
        dst_path = tmp / name
        if not src_path.exists() and not src_path.is_symlink():
            continue
        if dst_path.exists() or dst_path.is_symlink():
            dst_path.unlink()
        if src_path.is_symlink():
            dst_path.symlink_to(os.readlink(src_path))
        else:
            shutil.copy2(src_path, dst_path)


def run_benchmark(tmp_dir, root_dir, language, provider, model, enc_path):
    """run a single benchmark iteration, streaming output in realtime."""
    tmp = Path(tmp_dir)

    # touch src/enc.en to trigger rebuild
    (tmp / "src/enc.en").touch()

    # run make bootstrap-deps (silently, just touch targets)
    subprocess.run(
        ["make", "-s", "-t", "bootstrap-deps"],
        cwd=tmp,
        capture_output=True,
    )

    # run the transpilation
    env = os.environ.copy()
    env.update(
        {
            "ENC": enc_path,
            "PROVIDER": provider,
            "MODEL": model,
            "TEST_COMMAND": f"make test-{language}",
            "TEST_ITERATIONS": "5",
        }
    )

    # stream output in realtime while capturing for logging
    proc = subprocess.Popen(
        ["make", "-s", f"transpile-{language}"],
        cwd=tmp,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    output_lines = []
    if proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)
            output_lines.append(line)

    proc.wait()
    return proc.returncode, "".join(output_lines)


def parse_benchmark_output(output):
    """extract metrics from benchmark output."""
    attempts = len(re.findall(r"executing test command", output))

    cost_match = re.search(r"^total:\s*(\$[\d.]+)", output, re.MULTILINE)
    cost = parse_cost(cost_match.group(1) if cost_match else "N/A")

    time_match = re.search(r"^elapsed time:\s*([\d.]+s)", output, re.MULTILINE)
    elapsed = parse_time(time_match.group(1) if time_match else "N/A")

    token_match = re.search(r"^tokens:\s*(.+)$", output, re.MULTILINE)
    tokens = parse_tokens(token_match.group(1) if token_match else "N/A")

    log_match = re.search(r"^debug log path:\s*(.+)$", output, re.MULTILINE)
    debug_log = log_match.group(1).strip() if log_match else None

    return attempts, cost, elapsed, tokens, debug_log


def save_log(logs_dir, language, provider, model, run_num, output):
    """save benchmark log and return relative path."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    # sanitize model name for filename
    model_safe = model.replace("/", "-")
    filename = f"{language}-{provider}-{model_safe}-run{run_num}-{timestamp}.log"
    log_path = logs_dir / filename
    with open(log_path, "w") as f:
        f.write(output)
    return f"{LOGS_DIR}/{filename}", timestamp  # return timestamp for syncing


def save_debug_log(
    logs_dir, tmp_dir, relative_path, language, provider, model, run_num, timestamp
):
    """save debug log and return relative path."""
    if not relative_path:
        return None

    src_path = Path(tmp_dir) / relative_path
    if not src_path.exists():
        return None

    logs_dir.mkdir(parents=True, exist_ok=True)
    model_safe = model.replace("/", "-")
    filename = f"{language}-{provider}-{model_safe}-run{run_num}-{timestamp}.debug.log"
    dst_path = logs_dir / filename

    shutil.copy2(src_path, dst_path)
    return f"{LOGS_DIR}/{filename}"


def main():
    args = parse_args()

    root_dir = os.getcwd()
    enc_path = os.environ.get("ENC", os.path.join(root_dir, "target/release/enc"))
    benchmarks_dir = Path(root_dir) / BENCHMARKS_DIR
    results_path = benchmarks_dir / RESULTS_FILE
    logs_dir = benchmarks_dir / LOGS_DIR
    cleanup = os.environ.get("CLEANUP", "true").lower() == "true"

    benchmarks_dir.mkdir(parents=True, exist_ok=True)

    data = load_existing_results(results_path)
    lang_entry = get_or_create_language_entry(data, args.language)

    print(f"[*] using {enc_path} for benchmark ...")

    for model_pair in args.models:
        provider, model = model_pair.split("/", 1)
        print(f"[*] benchmarking {provider}/{model} ...")

        for i in range(1, args.iterations + 1):
            run_num = get_next_run_number(lang_entry["results"], provider, model)
            print(
                f"[*] starting benchmark run {i}/{args.iterations} (run #{run_num}) ..."
            )

            tmp_dir = tempfile.mkdtemp(prefix="enc-bench-")
            try:
                print(f"[*] running benchmark in {tmp_dir} ...")
                setup_benchmark_dir(tmp_dir, root_dir, args.language)

                exit_code, output = run_benchmark(
                    tmp_dir, root_dir, args.language, provider, model, enc_path
                )

                attempts, cost, elapsed, tokens, debug_log_path = (
                    parse_benchmark_output(output)
                )
                status = "PASS" if exit_code == 0 else "FAIL"

                log_path, timestamp = save_log(
                    logs_dir, args.language, provider, model, run_num, output
                )

                saved_debug_log_path = save_debug_log(
                    logs_dir,
                    tmp_dir,
                    debug_log_path,
                    args.language,
                    provider,
                    model,
                    run_num,
                    timestamp,
                )

                result = {
                    "provider": provider,
                    "model": model,
                    "run": run_num,
                    "attempts": attempts,
                    "status": status,
                    "cost": cost,
                    "time_seconds": elapsed,
                    "tokens": tokens,
                    "log": log_path,
                    "debug_log": saved_debug_log_path,
                }

                lang_entry["results"].append(result)
                save_results(results_path, data)

                print(
                    f"[*] run #{run_num}: {status} (cost: ${cost:.2f}, time: {elapsed:.1f}s)"
                )
                print(f"[*] log saved to {log_path}")
                if saved_debug_log_path:
                    print(f"[*] debug log saved to {saved_debug_log_path}")

            finally:
                if cleanup:
                    print(f"[*] cleaning up temporary dir {tmp_dir}")
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                else:
                    print(f"[*] skipping cleanup, kept {tmp_dir}")

    print(f"[*] benchmark completed! results written to {results_path}")


if __name__ == "__main__":
    main()

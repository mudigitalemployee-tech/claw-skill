#!/usr/bin/env python3
"""
Test Runner — Execute tests and capture structured results.

Usage:
    python3 scripts/run_tests.py <project-path> --framework <framework> [--test-dir tests] [--output results.json]

Supports: pytest, unittest, jest, mocha, vitest, junit5, go-test, rspec, cargo-test, phpunit

Output JSON:
{
  "framework": str,
  "command": str,
  "exit_code": int,
  "passed": int,
  "failed": int,
  "skipped": int,
  "errors": int,
  "total": int,
  "duration_seconds": float,
  "stdout": str,
  "stderr": str,
  "failures": [ { "test": str, "message": str } ]
}
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def build_command(framework: str, test_dir: str, project_path: str) -> list[str]:
    """Build the test execution command."""
    commands = {
        "pytest": ["python3", "-m", "pytest", test_dir, "-v", "--tb=short", "-q"],
        "unittest": ["python3", "-m", "unittest", "discover", "-s", test_dir, "-v"],
        "jest": ["npx", "jest", "--verbose", "--no-coverage", "--forceExit"],
        "mocha": ["npx", "mocha", f"{test_dir}/**/*.test.*", "--reporter", "spec"],
        "vitest": ["npx", "vitest", "run", "--reporter=verbose"],
        "junit5": ["mvn", "test", "-pl", "."],
        "go-test": ["go", "test", "./...", "-v", "-count=1"],
        "rspec": ["bundle", "exec", "rspec", test_dir, "--format", "documentation"],
        "cargo-test": ["cargo", "test", "--", "--nocapture"],
        "phpunit": ["./vendor/bin/phpunit", test_dir, "--verbose"],
        "xunit": ["dotnet", "test", "--verbosity", "normal"],
    }
    cmd = commands.get(framework)
    if not cmd:
        # Fallback: try pytest for Python, jest for JS
        cmd = ["python3", "-m", "pytest", test_dir, "-v", "--tb=short"]
    return cmd


def parse_pytest_output(stdout: str, stderr: str) -> dict:
    """Parse pytest output for structured results."""
    result = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "failures": []}

    # Parse summary line: "X passed, Y failed, Z skipped"
    summary = re.search(
        r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+error",
        stdout + stderr,
    )
    for m in re.finditer(r"(\d+)\s+(passed|failed|skipped|error)", stdout + stderr):
        count, kind = int(m.group(1)), m.group(2)
        if kind == "passed":
            result["passed"] = count
        elif kind == "failed":
            result["failed"] = count
        elif kind == "skipped":
            result["skipped"] = count
        elif kind == "error":
            result["errors"] = count

    # Extract failure details
    fail_blocks = re.findall(r"FAILED\s+([\w/:.]+(?:\[.*?\])?)", stdout + stderr)
    for fb in fail_blocks:
        result["failures"].append({"test": fb, "message": ""})

    # Try to get failure messages from short traceback
    for block in re.split(r"_{5,}\s+", stdout):
        name_match = re.search(r"FAILED\s+(.*?)(?:\s|$)", block)
        if name_match:
            name = name_match.group(1).strip()
            msg = block[:500].strip()
            for i, f in enumerate(result["failures"]):
                if f["test"] in name:
                    result["failures"][i]["message"] = msg
                    break

    return result


def parse_jest_output(stdout: str, stderr: str) -> dict:
    """Parse Jest output."""
    result = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "failures": []}
    combined = stdout + stderr

    for m in re.finditer(r"Tests:\s+(?:(\d+)\s+failed,\s+)?(?:(\d+)\s+skipped,\s+)?(?:(\d+)\s+passed,\s+)?(\d+)\s+total", combined):
        result["failed"] = int(m.group(1) or 0)
        result["skipped"] = int(m.group(2) or 0)
        result["passed"] = int(m.group(3) or 0)

    # Extract failure names
    for m in re.finditer(r"✕\s+(.+)", combined):
        result["failures"].append({"test": m.group(1).strip(), "message": ""})
    for m in re.finditer(r"FAIL\s+(.+)", combined):
        if not m.group(1).startswith("Test Suites"):
            result["failures"].append({"test": m.group(1).strip(), "message": ""})

    return result


def parse_go_output(stdout: str, stderr: str) -> dict:
    """Parse Go test output."""
    result = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "failures": []}
    combined = stdout + stderr

    for m in re.finditer(r"---\s+(PASS|FAIL|SKIP):\s+(\S+)", combined):
        status, name = m.group(1), m.group(2)
        if status == "PASS":
            result["passed"] += 1
        elif status == "FAIL":
            result["failed"] += 1
            result["failures"].append({"test": name, "message": ""})
        elif status == "SKIP":
            result["skipped"] += 1

    return result


def parse_generic_output(stdout: str, stderr: str) -> dict:
    """Generic parser — counts pass/fail keywords."""
    result = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "failures": []}
    combined = stdout + stderr

    result["passed"] = len(re.findall(r"\b(?:PASS(?:ED)?|✓|ok)\b", combined, re.IGNORECASE))
    result["failed"] = len(re.findall(r"\b(?:FAIL(?:ED)?|✕|ERRORS?)\b", combined, re.IGNORECASE))
    result["skipped"] = len(re.findall(r"\b(?:SKIP(?:PED)?|PENDING)\b", combined, re.IGNORECASE))

    return result


PARSERS = {
    "pytest": parse_pytest_output,
    "unittest": parse_pytest_output,  # similar format
    "jest": parse_jest_output,
    "vitest": parse_jest_output,  # similar format
    "go-test": parse_go_output,
}


def run_tests(project_path: str, framework: str, test_dir: str = "tests") -> dict:
    """Execute tests and return structured results."""
    cmd = build_command(framework, test_dir, project_path)

    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired:
        return {
            "framework": framework,
            "command": " ".join(cmd),
            "exit_code": -1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 1,
            "total": 0,
            "duration_seconds": 600.0,
            "stdout": "",
            "stderr": "Test execution timed out after 600 seconds",
            "failures": [{"test": "TIMEOUT", "message": "Execution exceeded 10 minute limit"}],
        }
    except FileNotFoundError:
        return {
            "framework": framework,
            "command": " ".join(cmd),
            "exit_code": -1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 1,
            "total": 0,
            "duration_seconds": 0.0,
            "stdout": "",
            "stderr": f"Command not found: {cmd[0]}. Ensure {framework} is installed.",
            "failures": [{"test": "SETUP", "message": f"{framework} not installed or not in PATH"}],
        }

    duration = time.time() - start

    parser = PARSERS.get(framework, parse_generic_output)
    parsed = parser(stdout, stderr)

    total = parsed["passed"] + parsed["failed"] + parsed["skipped"] + parsed["errors"]

    return {
        "framework": framework,
        "command": " ".join(cmd),
        "exit_code": exit_code,
        "passed": parsed["passed"],
        "failed": parsed["failed"],
        "skipped": parsed["skipped"],
        "errors": parsed["errors"],
        "total": total,
        "duration_seconds": round(duration, 2),
        "stdout": stdout[-5000:] if len(stdout) > 5000 else stdout,  # truncate
        "stderr": stderr[-3000:] if len(stderr) > 3000 else stderr,
        "failures": parsed["failures"],
    }


def main():
    parser = argparse.ArgumentParser(description="Run tests and capture results")
    parser.add_argument("project_path", help="Path to the project")
    parser.add_argument("--framework", "-f", required=True, help="Test framework to use")
    parser.add_argument("--test-dir", "-t", default="tests", help="Test directory (default: tests)")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    result = run_tests(args.project_path, args.framework, args.test_dir)

    output = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()

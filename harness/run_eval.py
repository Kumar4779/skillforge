"""SkillForge blind-eval grader (harness v0).

Grades a candidate patch against a task's hidden tests:

    1. Copy the task's project/ into a fresh temp workspace and git init it.
    2. Refuse (disqualify) any patch that touches test or test-harness files.
    3. Apply the patch.
    4. Copy hidden_tests/ in only after the patch is applied.
    5. Run pytest on the hidden tests. Execution is the ground truth.

Usage:
    python harness/run_eval.py --self-test
    python harness/run_eval.py TASK_DIR PATCH_FILE
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

HARNESS_DIR = Path(__file__).resolve().parent
TASK_001 = HARNESS_DIR / "fixtures" / "task-001"
PYTEST_TIMEOUT_S = 120

# Files that can change how tests are collected or run. Editing any of them is
# treated the same as editing a test.
_PROTECTED_NAMES = {"conftest.py", "pytest.ini", "sitecustomize.py", "usercustomize.py"}
_TEST_DIRS = {"test", "tests", "hidden_tests"}


def patch_paths(patch_diff: str) -> set[str]:
    """Return every file path a unified diff reads or writes."""
    paths = set()
    for line in patch_diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            candidates = parts[2:4]
        elif line.startswith(("--- ", "+++ ")):
            candidates = [line[4:].split("\t")[0]]
        elif line.startswith(("rename from ", "rename to ", "copy from ", "copy to ")):
            candidates = [line.split(" ", 2)[2]]
        else:
            continue
        for path in candidates:
            if path == "/dev/null":
                continue
            if path.startswith(("a/", "b/")):
                path = path[2:]
            paths.add(path)
    return paths


def disqualification(path: str) -> str | None:
    """Return why touching `path` disqualifies a patch, or None if it is allowed."""
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts:
        return f"patch touches a path outside the project: {path}"
    if any(part in _TEST_DIRS for part in pure.parts[:-1]):
        return f"patch touches a test file: {path}"
    name = pure.name
    if name.startswith("test_") or name.endswith("_test.py") or name in _PROTECTED_NAMES:
        return f"patch touches a test file: {path}"
    return None


def _record(passed: bool, disqualified: bool, reason: str, start: float) -> dict:
    return {
        "passed": passed,
        "disqualified": disqualified,
        "reason": reason,
        "duration_s": round(time.monotonic() - start, 3),
    }


def grade(task_dir: str | Path, patch_diff: str) -> dict:
    """Grade `patch_diff` against the task in `task_dir`.

    Returns {passed, disqualified, reason, duration_s}.
    """
    start = time.monotonic()
    task_dir = Path(task_dir)

    for path in sorted(patch_paths(patch_diff)):
        reason = disqualification(path)
        if reason:
            return _record(False, True, reason, start)

    with tempfile.TemporaryDirectory(prefix="skillforge-grade-") as tmp:
        workspace = Path(tmp) / "workspace"
        shutil.copytree(task_dir / "project", workspace)
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)

        if patch_diff.strip():
            patch_file = Path(tmp) / "candidate.diff"
            patch_file.write_text(patch_diff if patch_diff.endswith("\n") else patch_diff + "\n")
            applied = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", str(patch_file)],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            if applied.returncode != 0:
                return _record(False, False, f"patch did not apply: {applied.stderr.strip()}", start)

        # Hidden tests enter the workspace only after the candidate patch is applied.
        shutil.copytree(task_dir / "hidden_tests", workspace / "hidden_tests")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "hidden_tests"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=PYTEST_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return _record(False, False, f"hidden tests timed out after {PYTEST_TIMEOUT_S}s", start)

        summary = (result.stdout.strip().splitlines() or ["no pytest output"])[-1]
        if result.returncode == 0:
            return _record(True, False, f"hidden tests passed: {summary}", start)
        return _record(False, False, f"hidden tests failed: {summary}", start)


def make_test_edit_patch() -> str:
    """A patch that weakens a visible test. The grader must disqualify it."""
    return (
        "diff --git a/tests/test_durations.py b/tests/test_durations.py\n"
        "--- a/tests/test_durations.py\n"
        "+++ b/tests/test_durations.py\n"
        "@@ -2,7 +2,7 @@ from textkit import parse_duration\n"
        " \n"
        " \n"
        " def test_hours():\n"
        '-    assert parse_duration("2h") == 7200\n'
        "+    assert True\n"
        " \n"
        " \n"
        " def test_hours_and_minutes():\n"
    )


def self_test() -> int:
    gold = (TASK_001 / "gold_patch.diff").read_text()
    cases = [
        ("gold patch", gold, {"passed": True, "disqualified": False}),
        ("empty patch", "", {"passed": False, "disqualified": False}),
        ("test-edit patch", make_test_edit_patch(), {"passed": False, "disqualified": True}),
    ]
    failures = 0
    for name, patch, expected in cases:
        record = grade(TASK_001, patch)
        ok = all(record[key] == value for key, value in expected.items())
        failures += not ok
        print(f"[{'OK' if ok else 'FAIL'}] {name}: {json.dumps(record)}")
    print("self-test passed" if failures == 0 else f"self-test FAILED: {failures} case(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true", help="grade the built-in gold, empty, and test-edit patches")
    parser.add_argument("task_dir", nargs="?", help="task fixture directory")
    parser.add_argument("patch_file", nargs="?", help="unified diff to grade")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not (args.task_dir and args.patch_file):
        parser.error("give TASK_DIR and PATCH_FILE, or --self-test")
    record = grade(args.task_dir, Path(args.patch_file).read_text())
    print(json.dumps(record))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

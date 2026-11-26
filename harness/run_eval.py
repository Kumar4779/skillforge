"""SkillForge blind-eval grader (harness v0).

Grades a candidate patch against a task's hidden tests:

    1. Copy the task's project/ into a fresh temp workspace and git init it.
    2. Refuse (disqualify) any patch that touches test or test-harness files.
    3. Apply the patch.
    4. Copy hidden_tests/ in only after the patch is applied.
    5. Run pytest on the hidden tests. Execution is the ground truth.

Run mode (--run) drives a live A/B: for each trial, condition A runs Claude Code
headless on the task with no skill and condition B runs it with
skills/tdd-first-fix installed. Both conditions get the same prompt, tools,
permissions, and timeout. The resulting diff is graded with grade().

Usage:
    python harness/run_eval.py --self-test
    python harness/run_eval.py TASK_DIR PATCH_FILE
    python harness/run_eval.py --run --task harness/fixtures/task-001 --trials 1
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

HARNESS_DIR = Path(__file__).resolve().parent
TASK_001 = HARNESS_DIR / "fixtures" / "task-001"
PYTEST_TIMEOUT_S = 120

REPO_DIR = HARNESS_DIR.parent
SKILL_NAME = "tdd-first-fix"
AGENT_TIMEOUT_S = 600
AGENT_PROMPT = (
    "Read issue.md in this directory and fix the bug it describes. "
    "Work only inside this directory. Do not edit existing tests."
)
# Identical for both conditions. Edits are auto-accepted inside the workspace;
# Bash is limited to running Python/pytest and read-only git. User-level
# settings and MCP servers are excluded so they cannot differ between arms.
AGENT_COMMAND = [
    "claude", "-p", AGENT_PROMPT,
    "--output-format", "stream-json", "--verbose",
    "--permission-mode", "acceptEdits",
    "--allowedTools",
    "Read", "Edit", "Write", "Glob", "Grep", "Skill",
    "Bash(python:*)", "Bash(python3:*)", "Bash(pytest:*)",
    "Bash(git diff:*)", "Bash(git status:*)", "Bash(ls:*)",
    "--setting-sources", "project",
    "--strict-mcp-config",
    "--no-session-persistence",
]
# Workspace files that are part of the setup, not the candidate patch.
_SETUP_PATHS = ["issue.md", ".claude"]
_WORKSPACE_EXCLUDES = "__pycache__/\n*.pyc\n.pytest_cache/\n"

# Files that can change how tests are collected or run. Editing any of them is
# treated the same as editing a test.
_PROTECTED_NAMES = {"conftest.py", "pytest.ini", "sitecustomize.py", "usercustomize.py"}
_TEST_DIRS = {"test", "tests", "hidden_tests"}
# Project config files that can carry pytest settings (addopts, testpaths, plugins).
_TEST_CONFIG_NAMES = {"pyproject.toml", "setup.cfg", "tox.ini"}


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
    if name in _TEST_CONFIG_NAMES:
        return f"patch touches test configuration: {path}"
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


def _git(workspace: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=skillforge", "-c", "user.email=harness@skillforge.invalid", *args],
        cwd=workspace, check=True, capture_output=True, text=True,
    ).stdout


def _prepare_workspace(task_dir: Path, workspace: Path, with_skill: bool) -> None:
    shutil.copytree(task_dir / "project", workspace)
    _git(workspace, "init", "-q")
    (workspace / ".git" / "info" / "exclude").write_text(_WORKSPACE_EXCLUDES)
    if with_skill:
        shutil.copytree(REPO_DIR / "skills" / SKILL_NAME, workspace / ".claude" / "skills" / SKILL_NAME)
    shutil.copy(task_dir / "issue.md", workspace / "issue.md")
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-q", "-m", "baseline")


def _captured_diff(workspace: Path) -> str:
    _git(workspace, "add", "-A")
    excludes = [f":(exclude){path}" for path in _SETUP_PATHS]
    return _git(workspace, "diff", "--cached", "HEAD", "--", ".", *excludes)


def _summarize_transcript(stream: str) -> dict:
    """Pull turn count, cost, and skill usage out of a stream-json transcript."""
    summary = {"skill_invoked": False, "skills_available": None, "num_turns": None,
               "total_cost_usd": None, "agent_is_error": None}
    for line in stream.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            summary["skills_available"] = event.get("skills")
        elif event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "Skill":
                    summary["skill_invoked"] = True
        elif event.get("type") == "result":
            summary["num_turns"] = event.get("num_turns")
            summary["total_cost_usd"] = event.get("total_cost_usd")
            summary["agent_is_error"] = event.get("is_error")
    return summary


def run_trial(task_dir: Path, condition: str, trial: int) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"skillforge-{condition}-") as tmp:
        workspace = Path(tmp) / "workspace"
        _prepare_workspace(task_dir, workspace, with_skill=(condition == "B"))
        # Strip the parent Claude Code session's variables so the child starts clean.
        env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
        start = time.monotonic()
        timed_out = False
        try:
            agent = subprocess.run(AGENT_COMMAND, cwd=workspace, env=env, capture_output=True,
                                   text=True, timeout=AGENT_TIMEOUT_S)
            stream, exit_code = agent.stdout, agent.returncode
        except subprocess.TimeoutExpired as exc:
            stream = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            exit_code, timed_out = None, True
        agent_duration = round(time.monotonic() - start, 3)
        diff = _captured_diff(workspace)

    graded = grade(task_dir, diff)
    return {
        "condition": condition,
        "skill": SKILL_NAME if condition == "B" else None,
        "trial": trial,
        "passed": graded["passed"],
        "disqualified": graded["disqualified"],
        "reason": graded["reason"],
        "duration_s": agent_duration,
        "grade_duration_s": graded["duration_s"],
        "agent_exit_code": exit_code,
        "agent_timed_out": timed_out,
        **_summarize_transcript(stream),
        "diff": diff,
    }


def small_sample_note(trials: int) -> str:
    return (
        f"n={trials} per condition. This proves the eval loop runs end to end; it is NOT evidence "
        "the skill works. Skill verdicts require at least 3 trials per condition."
    )


def run_ab(task_dir: Path, trials: int) -> list[dict]:
    records = []
    for trial in range(1, trials + 1):
        for condition in ("A", "B"):
            print(f"running condition {condition}, trial {trial} ...", flush=True)
            records.append(run_trial(task_dir, condition, trial))
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true", help="grade the built-in gold, empty, and test-edit patches")
    parser.add_argument("--run", action="store_true", help="run a live A/B with Claude Code headless")
    parser.add_argument("--task", help="task fixture directory for --run")
    parser.add_argument("--trials", type=int, default=1, help="trials per condition for --run")
    parser.add_argument("--out", help="results JSON for --run (default: harness/results/<task>-ab-smoke.json "
                                      "below 3 trials, otherwise <task>-ab-n<trials>.json)")
    parser.add_argument("task_dir", nargs="?", help="task fixture directory")
    parser.add_argument("patch_file", nargs="?", help="unified diff to grade")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.run:
        if not args.task:
            parser.error("--run needs --task")
        records = run_ab(Path(args.task), args.trials)
        for record in records:
            print(json.dumps({k: v for k, v in record.items() if k != "diff"}))
        task_name = Path(args.task).name
        suffix = "ab-smoke" if args.trials < 3 else f"ab-n{args.trials}"
        out = Path(args.out) if args.out else HARNESS_DIR / "results" / f"{task_name}-{suffix}.json"
        results = {"task": task_name, "trials_per_condition": args.trials,
                   "agent_command": AGENT_COMMAND, "records": records}
        if args.trials < 3:
            results = {"note": small_sample_note(args.trials), **results}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2) + "\n")
        print(f"wrote {out}")
        return 0
    if not (args.task_dir and args.patch_file):
        parser.error("give TASK_DIR and PATCH_FILE, or --self-test")
    record = grade(args.task_dir, Path(args.patch_file).read_text())
    print(json.dumps(record))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

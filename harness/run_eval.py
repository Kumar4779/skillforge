"""SkillForge blind-eval grader (harness v0).

Grades a candidate patch against a task's hidden tests:

    1. Copy the task's project/ into a fresh temp workspace and git init it.
    2. Refuse (disqualify) patches that change existing tests, hidden tests, or test
       configuration. Adding new tests is allowed (grader rule v2).
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
    python harness/run_eval.py --scored --trials 3
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

HARNESS_DIR = Path(__file__).resolve().parent
TASK_001 = HARNESS_DIR / "fixtures" / "task-001"
PYTEST_TIMEOUT_S = 120
GRADER_RULE = "v2 (line-aware)"

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

# Grader rule v2 (line-aware):
#   - Paths outside the project, hidden_tests/, and test configuration: always disqualify.
#   - New test files: allowed. The hidden tests, kept outside the workspace, decide pass/fail.
#   - Existing test files: allowed only as pure additions. Removing, changing, renaming, or
#     deleting existing test content disqualifies.
_TEST_CONFIG_NAMES = {
    "conftest.py", "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini",
    "sitecustomize.py", "usercustomize.py",
}
_TEST_DIRS = {"test", "tests"}
# Modules that, once added, shadow the test runner or run code at interpreter start-up.
_SHADOW_FILE_NAMES = {"pytest.py", "usercustomize.py"}
_SHADOW_PACKAGE_NAMES = {"pytest"}
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")


@dataclass
class FileChange:
    old_path: str | None  # None when the file is created
    new_path: str | None  # None when the file is deleted
    added: int = 0
    removed: int = 0

    @property
    def paths(self) -> set[str]:
        return {path for path in (self.old_path, self.new_path) if path}


def _strip_prefix(path: str) -> str | None:
    path = path.split("\t")[0]
    if path == "/dev/null":
        return None
    return path[2:] if path.startswith(("a/", "b/")) else path


def parse_patch(patch_diff: str) -> list[FileChange]:
    """Split a unified diff into per-file changes with added/removed line counts.

    Hunks are consumed by the line counts in their @@ headers, so a removed line whose
    content starts with "-- " is never mistaken for a file header.
    """
    changes: list[FileChange] = []
    current: FileChange | None = None
    lines = patch_diff.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            parts = line.split()
            current = FileChange(_strip_prefix(parts[2]), _strip_prefix(parts[3]))
            changes.append(current)
        elif line.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            if current is None or current.added or current.removed:
                current = FileChange(None, None)
                changes.append(current)
            current.old_path = _strip_prefix(line[4:])
            current.new_path = _strip_prefix(lines[i + 1][4:])
            i += 1
        elif line.startswith(("new file mode", "deleted file mode")) and current is not None:
            if line.startswith("new"):
                current.old_path = None
            else:
                current.new_path = None
        elif line.startswith(("rename from ", "copy from ")) and current is not None:
            current.old_path = line.split(" ", 2)[2]
        elif line.startswith(("rename to ", "copy to ")) and current is not None:
            current.new_path = line.split(" ", 2)[2]
        elif (match := _HUNK_HEADER.match(line)) and current is not None:
            old_left = int(match.group(1) or 1)
            new_left = int(match.group(2) or 1)
            while (old_left > 0 or new_left > 0) and i + 1 < len(lines):
                i += 1
                body = lines[i]
                if body.startswith("\\"):  # "\ No newline at end of file"
                    continue
                if body.startswith("-"):
                    current.removed += 1
                    old_left -= 1
                elif body.startswith("+"):
                    current.added += 1
                    new_left -= 1
                else:
                    old_left -= 1
                    new_left -= 1
        i += 1
    return changes


def is_test_path(path: str) -> bool:
    pure = PurePosixPath(path)
    name = pure.name
    return (
        any(part in _TEST_DIRS for part in pure.parts[:-1])
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def disqualification(change: FileChange, project_dir: Path) -> str | None:
    """Return why `change` disqualifies the patch, or None if it is allowed."""
    added = change.new_path if change.new_path and change.new_path != change.old_path else None
    if added:
        pure = PurePosixPath(added)
        if pure.name in _SHADOW_FILE_NAMES or any(part in _SHADOW_PACKAGE_NAMES for part in pure.parts[:-1]):
            return f"patch adds a module that shadows the test runner: {added}"

    for path in sorted(change.paths):
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts:
            return f"patch touches a path outside the project: {path}"
        if "hidden_tests" in pure.parts:
            return f"patch touches hidden tests: {path}"
        if pure.name in _TEST_CONFIG_NAMES:
            return f"patch touches test configuration: {path}"

    old = change.old_path
    if old and is_test_path(old) and (project_dir / old).exists():
        if change.removed or change.new_path != old:
            return f"patch modifies existing test content: {old}"
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

    for change in parse_patch(patch_diff):
        reason = disqualification(change, task_dir / "project")
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


def make_patch(task_dir: Path, files: dict[str, str | None]) -> str:
    """Build a real git diff against task_dir/project. Map path -> new content, or None to delete."""
    with tempfile.TemporaryDirectory(prefix="skillforge-patch-") as tmp:
        workspace = Path(tmp) / "workspace"
        shutil.copytree(task_dir / "project", workspace)
        _git(workspace, "init", "-q")
        _git(workspace, "add", "-A")
        _git(workspace, "commit", "-q", "-m", "base")
        for path, content in files.items():
            target = workspace / path
            if content is None:
                target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
        _git(workspace, "add", "-A")
        return _git(workspace, "diff", "--cached", "HEAD")


def task_001_cases() -> list[tuple[str, str, dict]]:
    """Patches for task-001 and the grade each must get. Shared by --self-test and pytest."""
    project = TASK_001 / "project"
    durations = (project / "textkit" / "durations.py").read_text()
    tests = (project / "tests" / "test_durations.py").read_text()
    fix = {"textkit/durations.py": durations.replace(
        "return hours * 3600 + minutes * 60\n", "return hours * 3600 + minutes * 60 + seconds\n")}
    new_test = "from textkit import parse_duration\n\n\ndef test_seconds():\n    assert parse_duration(\"45s\") == 45\n"
    appended = tests + "\n\ndef test_seconds():\n    assert parse_duration(\"45s\") == 45\n"
    changed_line = tests.replace('assert parse_duration("2h") == 7200', "assert True")
    deleted_test = tests.replace('def test_hours():\n    assert parse_duration("2h") == 7200\n\n\n', "")
    pyproject = (project / "pyproject.toml").read_text() + '\n[tool.pytest.ini_options]\naddopts = "-p no:randomly"\n'

    passes = {"passed": True, "disqualified": False}
    fails = {"passed": False, "disqualified": False}
    dq = {"passed": False, "disqualified": True}
    return [
        ("gold patch", (TASK_001 / "gold_patch.diff").read_text(), passes),
        ("empty patch", "", fails),
        ("new test file + fix", make_patch(TASK_001, {**fix, "tests/test_seconds.py": new_test}), passes),
        ("appended test + fix", make_patch(TASK_001, {**fix, "tests/test_durations.py": appended}), passes),
        ("changed existing test line + fix",
         make_patch(TASK_001, {**fix, "tests/test_durations.py": changed_line}),
         {**dq, "reason": "patch modifies existing test content: tests/test_durations.py"}),
        ("deleted existing test + fix",
         make_patch(TASK_001, {**fix, "tests/test_durations.py": deleted_test}),
         {**dq, "reason": "patch modifies existing test content: tests/test_durations.py"}),
        ("pyproject.toml edit + fix", make_patch(TASK_001, {**fix, "pyproject.toml": pyproject}),
         {**dq, "reason": "patch touches test configuration: pyproject.toml"}),
        ("pytest.py shadow + fix",
         make_patch(TASK_001, {**fix, "pytest.py": "def main():\n    raise SystemExit(0)\n"}),
         {**dq, "reason": "patch adds a module that shadows the test runner: pytest.py"}),
    ]


def self_test() -> int:
    cases = task_001_cases()
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
        "task": task_dir.name,
        "grader_rule": GRADER_RULE,
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


SCORED_NOTE = (
    "3 tasks x 3 trials per arm. Small sample — directional, not conclusive. "
    "Both arms also have the host's built-in skills available."
)


def task_dirs() -> list[Path]:
    return sorted(path for path in (HARNESS_DIR / "fixtures").iterdir() if path.is_dir())


def _arm_summary(records: list[dict]) -> dict:
    passes = sum(record["passed"] for record in records)
    costs = [record.get("total_cost_usd") for record in records]
    total_cost = round(sum(cost or 0.0 for cost in costs), 6)
    return {
        "passes": passes,
        "trials": len(records),
        "pass_rate": round(passes / len(records), 4) if records else None,
        "disqualified": sum(record["disqualified"] for record in records),
        "timed_out": sum(record["agent_timed_out"] for record in records),
        "total_cost_usd": total_cost,
        "cost_per_solved_task_usd": round(total_cost / passes, 6) if passes else "no solves",
        "runs_missing_cost": sum(cost is None for cost in costs),
    }


def summarize_scored(records: list[dict]) -> dict:
    """Per-task and overall pass counts, pass^k, and cost per arm."""
    tasks = sorted({record["task"] for record in records})
    per_task = {}
    for task in tasks:
        per_task[task] = {}
        for arm in ("A", "B"):
            arm_records = [r for r in records if r["task"] == task and r["condition"] == arm]
            summary = _arm_summary(arm_records)
            summary["pass_hat_k"] = bool(arm_records) and summary["passes"] == summary["trials"]
            per_task[task][arm] = summary
    overall = {}
    for arm in ("A", "B"):
        summary = _arm_summary([r for r in records if r["condition"] == arm])
        summary["tasks_with_pass_hat_k"] = sum(per_task[task][arm]["pass_hat_k"] for task in tasks)
        summary["tasks"] = len(tasks)
        overall[arm] = summary
    return {"per_task": per_task, "overall": overall}


def _next_scored_path() -> Path:
    """First unused harness/results/<skill>-scored-vN.json, so earlier runs are never overwritten."""
    version = 1
    while (path := HARNESS_DIR / "results" / f"{SKILL_NAME}-scored-v{version}.json").exists():
        version += 1
    return path


def run_scored(trials: int) -> list[dict]:
    records = []
    for task_dir in task_dirs():
        for trial in range(1, trials + 1):
            for condition in ("A", "B"):
                print(f"running {task_dir.name}, condition {condition}, trial {trial} ...", flush=True)
                record = run_trial(task_dir, condition, trial)
                print(json.dumps({k: v for k, v in record.items() if k not in ("diff", "skills_available")}),
                      flush=True)
                records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true", help="grade the built-in gold, empty, and test-edit patches")
    parser.add_argument("--run", action="store_true", help="run a live A/B with Claude Code headless")
    parser.add_argument("--scored", action="store_true",
                        help="run every task in harness/fixtures/, both arms, --trials each, and summarize")
    parser.add_argument("--task", help="task fixture directory for --run")
    parser.add_argument("--trials", type=int, default=1, help="trials per condition for --run / --scored")
    parser.add_argument("--out", help="results JSON for --run (default: harness/results/<task>-ab-smoke.json "
                                      "below 3 trials, otherwise <task>-ab-n<trials>.json)")
    parser.add_argument("task_dir", nargs="?", help="task fixture directory")
    parser.add_argument("patch_file", nargs="?", help="unified diff to grade")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.scored:
        records = run_scored(args.trials)
        out = Path(args.out) if args.out else _next_scored_path()
        results = {
            "note": SCORED_NOTE,
            "skill": SKILL_NAME,
            "grader_rule": GRADER_RULE,
            "tasks": [path.name for path in task_dirs()],
            "trials_per_condition": args.trials,
            "agent_command": AGENT_COMMAND,
            "agent_timeout_s": AGENT_TIMEOUT_S,
            "summary": summarize_scored(records),
            "records": records,
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps(results["summary"], indent=2))
        print(f"wrote {out}")
        return 0
    if args.run:
        if not args.task:
            parser.error("--run needs --task")
        records = run_ab(Path(args.task), args.trials)
        for record in records:
            print(json.dumps({k: v for k, v in record.items() if k != "diff"}))
        task_name = Path(args.task).name
        suffix = "ab-smoke" if args.trials < 3 else f"ab-n{args.trials}"
        out = Path(args.out) if args.out else HARNESS_DIR / "results" / f"{task_name}-{suffix}.json"
        results = {"task": task_name, "grader_rule": GRADER_RULE, "trials_per_condition": args.trials,
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

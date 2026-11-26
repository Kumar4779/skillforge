import json
import re
import sys
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HARNESS_DIR))

import run_eval  # noqa: E402
from run_eval import TASK_001, grade, make_patch, parse_patch, summarize_scored, task_001_cases  # noqa: E402

FIXTURES = HARNESS_DIR / "fixtures"
TASK_DIRS = sorted(path for path in FIXTURES.iterdir() if path.is_dir())
CASES = {name: (patch, expected) for name, patch, expected in task_001_cases()}


def _assert_grade(name):
    patch, expected = CASES[name]
    record = grade(TASK_001, patch)
    for key, value in expected.items():
        assert record[key] == value, f"{name}: {key}={record[key]!r}, reason={record['reason']!r}"
    return record


def test_gold_patch_passes():
    _assert_grade("gold patch")


def test_empty_patch_fails_without_disqualification():
    record = _assert_grade("empty patch")
    assert record["reason"].startswith("hidden tests failed")


def test_new_test_file_with_fix_passes():
    _assert_grade("new test file + fix")


def test_appended_test_with_fix_passes():
    _assert_grade("appended test + fix")


def test_changed_existing_test_line_is_disqualified():
    _assert_grade("changed existing test line + fix")


def test_deleted_existing_test_is_disqualified():
    _assert_grade("deleted existing test + fix")


def test_pyproject_edit_is_disqualified():
    _assert_grade("pyproject.toml edit + fix")


def test_pytest_shadow_module_is_disqualified():
    _assert_grade("pytest.py shadow + fix")


@pytest.mark.parametrize(
    "path",
    ["textkit/pytest.py", "pytest/__init__.py", "pytest/main.py", "usercustomize.py"],
)
def test_other_shadow_modules_are_disqualified(path):
    patch = f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n+++ b/{path}\n@@ -0,0 +1 @@\n+x = 1\n"
    record = grade(TASK_001, patch)
    assert record["disqualified"] is True
    assert record["reason"] == f"patch adds a module that shadows the test runner: {path}"


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("hidden_tests/test_hidden_durations.py", "patch touches hidden tests: hidden_tests/test_hidden_durations.py"),
        ("tests/conftest.py", "patch touches test configuration: tests/conftest.py"),
        ("../outside.py", "patch touches a path outside the project: ../outside.py"),
    ],
)
def test_protected_paths_are_disqualified_even_as_new_files(path, reason):
    patch = f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n+++ b/{path}\n@@ -0,0 +1 @@\n+x = 1\n"
    record = grade(TASK_001, patch)
    assert record["disqualified"] is True
    assert record["reason"] == reason


def test_deleting_an_existing_test_file_is_disqualified():
    patch = (
        "diff --git a/tests/test_durations.py b/tests/test_durations.py\n"
        "deleted file mode 100644\n"
        "--- a/tests/test_durations.py\n"
        "+++ /dev/null\n"
        "@@ -1,2 +0,0 @@\n"
        "-from textkit import parse_duration\n"
        "-\n"
    )
    record = grade(TASK_001, patch)
    assert record["disqualified"] is True
    assert record["reason"] == "patch modifies existing test content: tests/test_durations.py"


def test_parser_does_not_mistake_removed_dash_lines_for_headers():
    patch = (
        "diff --git a/notes.txt b/notes.txt\n"
        "--- a/notes.txt\n"
        "+++ b/notes.txt\n"
        "@@ -1 +1 @@\n"
        "--- a removed line that starts with dashes\n"
        "+++ an added line that starts with pluses\n"
    )
    [change] = parse_patch(patch)
    assert (change.old_path, change.new_path, change.added, change.removed) == ("notes.txt", "notes.txt", 1, 1)


def test_record_shape():
    record = grade(TASK_001, "")
    assert set(record) == {"passed", "disqualified", "reason", "duration_s"}
    assert isinstance(record["duration_s"], float)


@pytest.mark.parametrize("task_dir", TASK_DIRS, ids=lambda path: path.name)
def test_every_task_gold_passes_and_empty_fails(task_dir):
    gold = grade(task_dir, (task_dir / "gold_patch.diff").read_text())
    assert (gold["passed"], gold["disqualified"]) == (True, False), gold["reason"]
    empty = grade(task_dir, "")
    assert (empty["passed"], empty["disqualified"]) == (False, False), empty["reason"]


def test_task_002_tempting_in_place_sort_fix_fails():
    task_dir = FIXTURES / "task-002"
    stats = (task_dir / "project" / "statkit" / "stats.py").read_text()
    tempting = stats.replace(
        "    return values[len(values) // 2]\n",
        "    middle = len(values) // 2\n"
        "    if len(values) % 2:\n"
        "        return values[middle]\n"
        "    return (values[middle - 1] + values[middle]) / 2\n",
    )
    record = grade(task_dir, make_patch(task_dir, {"statkit/stats.py": tempting}))
    assert (record["passed"], record["disqualified"]) == (False, False)
    assert "1 failed" in record["reason"]


def _fake(task, condition, passed, cost, disqualified=False):
    return {"task": task, "condition": condition, "passed": passed, "disqualified": disqualified,
            "agent_timed_out": False, "total_cost_usd": cost}


def test_summarize_scored_counts_pass_hat_k_and_cost_per_solve():
    records = [
        _fake("t1", "A", True, 0.1), _fake("t1", "A", True, 0.1), _fake("t1", "A", True, 0.1),
        _fake("t1", "B", True, 0.2), _fake("t1", "B", False, 0.2, disqualified=True), _fake("t1", "B", True, 0.2),
        _fake("t2", "A", False, 0.3), _fake("t2", "A", False, 0.3), _fake("t2", "A", False, None),
        _fake("t2", "B", True, 0.4), _fake("t2", "B", True, 0.4), _fake("t2", "B", True, 0.4),
    ]
    summary = summarize_scored(records)
    t1a, t1b = summary["per_task"]["t1"]["A"], summary["per_task"]["t1"]["B"]
    t2a, t2b = summary["per_task"]["t2"]["A"], summary["per_task"]["t2"]["B"]
    assert (t1a["passes"], t1a["trials"], t1a["pass_hat_k"]) == (3, 3, True)
    assert (t1b["passes"], t1b["pass_hat_k"], t1b["disqualified"]) == (2, False, 1)
    assert t1b["cost_per_solved_task_usd"] == pytest.approx(0.3)
    assert t2a["cost_per_solved_task_usd"] == "no solves"
    assert t2a["runs_missing_cost"] == 1
    assert t2b["pass_hat_k"] is True
    overall_a, overall_b = summary["overall"]["A"], summary["overall"]["B"]
    assert (overall_a["passes"], overall_a["trials"], overall_a["tasks_with_pass_hat_k"]) == (3, 6, 1)
    assert (overall_b["passes"], overall_b["trials"], overall_b["tasks_with_pass_hat_k"]) == (5, 6, 1)
    assert overall_b["total_cost_usd"] == pytest.approx(1.8)
    assert overall_b["cost_per_solved_task_usd"] == pytest.approx(0.36)


def test_skill_version_records_commit_and_installed_file_hash(tmp_path):
    workspace = tmp_path / "workspace"
    run_eval._prepare_workspace(TASK_001, workspace, with_skill=True)
    installed = workspace / ".claude" / "skills" / run_eval.SKILL_NAME / "SKILL.md"
    sha = run_eval.file_sha256_12(installed)
    records = [{"condition": "A", "skill_sha256_12": None}, {"condition": "B", "skill_sha256_12": sha}]

    version = run_eval.skill_version(records)

    assert set(version) == {"commit", "sha256_12", "uncommitted_changes"}
    assert re.fullmatch(r"[0-9a-f]{7,40}", version["commit"])
    assert version["sha256_12"] == sha
    assert re.fullmatch(r"[0-9a-f]{12}", sha)
    assert sha == run_eval.file_sha256_12(run_eval.REPO_DIR / "skills" / run_eval.SKILL_NAME / "SKILL.md")
    assert isinstance(version["uncommitted_changes"], bool)


def test_skill_version_rejects_mixed_skill_texts():
    records = [{"condition": "B", "skill_sha256_12": "aaaaaaaaaaaa"}, {"condition": "B", "skill_sha256_12": "bbbbbbbbbbbb"}]
    with pytest.raises(RuntimeError, match="different SKILL.md texts"):
        run_eval.skill_version(records)


def test_task_filter_selects_only_named_tasks():
    selected = run_eval.task_dirs(["task-004", "task-005", "task-006"])
    assert [path.name for path in selected] == ["task-004", "task-005", "task-006"]
    assert all(path.parent == run_eval.HARNESS_DIR / "fixtures" for path in selected)


def test_task_filter_defaults_to_all_fixtures_and_rejects_unknown_names():
    assert [path.name for path in run_eval.task_dirs()] == [path.name for path in TASK_DIRS]
    with pytest.raises(ValueError, match="unknown task"):
        run_eval.task_dirs(["task-004", "task-999"])


def test_scored_cli_runs_only_filtered_tasks_and_writes_chosen_path(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "AGENT_COMMAND", ["true"])
    out = tmp_path / "scored.json"
    monkeypatch.setattr(sys, "argv", ["run_eval.py", "--scored", "--trials", "1", "--tasks", "task-005,task-006",
                                      "--out", str(out), "--note", "custom note"])
    assert run_eval.main() == 0
    results = json.loads(out.read_text())
    assert results["tasks"] == ["task-005", "task-006"]
    assert sorted({r["task"] for r in results["records"]}) == ["task-005", "task-006"]
    assert len(results["records"]) == 4
    assert results["note"] == "custom note"
    assert set(results["summary"]["per_task"]) == {"task-005", "task-006"}

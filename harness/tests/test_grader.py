import sys
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HARNESS_DIR))

from run_eval import TASK_001, grade, parse_patch, task_001_cases  # noqa: E402

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

import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HARNESS_DIR))

from run_eval import TASK_001, grade, make_test_edit_patch  # noqa: E402


def test_gold_patch_passes():
    record = grade(TASK_001, (TASK_001 / "gold_patch.diff").read_text())
    assert record["passed"] is True
    assert record["disqualified"] is False


def test_empty_patch_fails_without_disqualification():
    record = grade(TASK_001, "")
    assert record["passed"] is False
    assert record["disqualified"] is False
    assert record["reason"].startswith("hidden tests failed")


def test_test_edit_patch_is_disqualified():
    record = grade(TASK_001, make_test_edit_patch())
    assert record["passed"] is False
    assert record["disqualified"] is True
    assert "tests/test_durations.py" in record["reason"]


def test_record_shape():
    record = grade(TASK_001, "")
    assert set(record) == {"passed", "disqualified", "reason", "duration_s"}
    assert isinstance(record["duration_s"], float)


def test_pyproject_edit_is_disqualified():
    patch = (
        "diff --git a/pyproject.toml b/pyproject.toml\n"
        "--- a/pyproject.toml\n"
        "+++ b/pyproject.toml\n"
        "@@ -2,3 +2,6 @@\n"
        ' name = "textkit"\n'
        ' version = "0.1.0"\n'
        ' requires-python = ">=3.10"\n'
        "+\n"
        "+[tool.pytest.ini_options]\n"
        '+addopts = "--deselect hidden_tests"\n'
    )
    record = grade(TASK_001, patch)
    assert record["passed"] is False
    assert record["disqualified"] is True
    assert record["reason"] == "patch touches test configuration: pyproject.toml"

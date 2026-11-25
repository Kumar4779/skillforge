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

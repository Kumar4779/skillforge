# Harness

**Status:** Grader built and self-tested. No live agent runs yet. Results will be published under `harness/results/` when they exist.

## What exists

- `run_eval.py` — `grade(task_dir, patch_diff)` copies a task's `project/` into a fresh temp git workspace, applies the candidate patch, copies in `hidden_tests/`, and runs pytest on them. It returns `{passed, disqualified, reason, duration_s}`.
- Patches that touch a test file, anything under `hidden_tests/`, test-config files (`conftest.py`, `pytest.ini`), or paths outside the project are disqualified before they are applied.
- `fixtures/task-001/` — the first eval task: a `textkit` package whose `parse_duration` drops the seconds component. It contains `project/`, `issue.md`, `hidden_tests/`, and `gold_patch.diff`. The hidden tests are never copied into an agent's workspace.
- `tests/test_grader.py` — checks that the gold patch passes, an empty patch fails, and a test-editing patch is disqualified. CI runs these on every push and pull request.

## Usage

```
python harness/run_eval.py --self-test
python harness/run_eval.py harness/fixtures/task-001 path/to/patch.diff
```

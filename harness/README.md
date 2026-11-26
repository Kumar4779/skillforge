# Harness

**Status:** Grader self-tested. Disqualification covers test files and test configuration. First live A/B smoke run recorded in `harness/results/task-001-ab-smoke.json` (n=1 per condition — pipeline proof only, not evidence the skill works). Further results will be published under `harness/results/`.

## What exists

- `run_eval.py` — `grade(task_dir, patch_diff)` copies a task's `project/` into a fresh temp git workspace, applies the candidate patch, copies in `hidden_tests/`, and runs pytest on them. It returns `{passed, disqualified, reason, duration_s}`.
- Patches that touch a test file, anything under `hidden_tests/`, test configuration (`conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`), or paths outside the project are disqualified before they are applied.
- `--run` drives a live A/B: condition A runs Claude Code headless with no skill, condition B with `skills/tdd-first-fix` installed at `.claude/skills/`. Both get the same prompt, tools, permissions, and 10-minute timeout; the resulting diff is graded with `grade()`.
- `fixtures/task-001/` — the first eval task: a `textkit` package whose `parse_duration` drops the seconds component. It contains `project/`, `issue.md`, `hidden_tests/`, and `gold_patch.diff`. The hidden tests are never copied into an agent's workspace.
- `tests/test_grader.py` — checks that the gold patch passes, an empty patch fails, and a test-editing patch is disqualified. CI runs these on every push and pull request.

## Usage

```
python harness/run_eval.py --self-test
python harness/run_eval.py harness/fixtures/task-001 path/to/patch.diff
python harness/run_eval.py --run --task harness/fixtures/task-001 --trials 1
```

# Harness

**Status:** Grader self-tested under grader rule v2 (line-aware). Disqualification covers changes to existing test lines, hidden tests, and test configuration; adding new tests is allowed. Live A/B smoke runs recorded: `harness/results/task-001-ab-smoke.json` (rule v1 — both arms disqualified for writing tests, which v2 corrects) and `harness/results/task-001-ab-smoke-v2.json` (rule v2). Both are n=1 per condition: pipeline proof only, not evidence the skill works. First scored run recorded for `tdd-first-fix`: `harness/results/tdd-first-fix-scored-v1.json` (3 tasks x 3 trials per arm; small sample). Further results will be published under `harness/results/`.

## What exists

- `run_eval.py` — `grade(task_dir, patch_diff)` copies a task's `project/` into a fresh temp git workspace, applies the candidate patch, copies in `hidden_tests/`, and runs pytest on them. It returns `{passed, disqualified, reason, duration_s}`.
- Grader rule v2 (line-aware), checked before the patch is applied: new test files and pure additions to existing test files are allowed. Disqualified: removing or changing existing test lines, deleting or renaming an existing test file, touching `hidden_tests/`, adding or editing test configuration (`conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`, `sitecustomize.py`), and paths outside the project.
- `--run` drives a live A/B: condition A runs Claude Code headless with no skill, condition B with `skills/tdd-first-fix` installed at `.claude/skills/`. Both get the same prompt, tools, permissions, and 10-minute timeout; the resulting diff is graded with `grade()`.
- `fixtures/task-001/` — the first eval task: a `textkit` package whose `parse_duration` drops the seconds component. It contains `project/`, `issue.md`, `hidden_tests/`, and `gold_patch.diff`. The hidden tests are never copied into an agent's workspace.
- `fixtures/task-002/` — `statkit.median` returns the upper middle for even-length lists; the minimal fix that keeps the existing in-place sort still fails a hidden no-mutation test. `fixtures/task-003/` — `cachekit.LRUCache.get` does not refresh recency, so a just-read key is evicted. Both are gold-verified (gold passes, empty fails).
- `tests/test_grader.py` — checks the gold patch passes, an empty patch fails, added tests are allowed, changed or deleted existing tests and test-config edits are disqualified, and protected paths are refused. `--self-test` runs the same task-001 cases. CI runs the tests on every push and pull request.
- Known confound: Claude Code's built-in skills are available in both arms equally (see SPEC.md §4.6).

## Usage

```
python harness/run_eval.py --self-test
python harness/run_eval.py harness/fixtures/task-001 path/to/patch.diff
python harness/run_eval.py --run --task harness/fixtures/task-001 --trials 1
python harness/run_eval.py --scored --trials 3
```

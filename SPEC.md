# SkillForge Specification

## 1. Goals

1. Provide a small library of portable `SKILL.md` files that change how a coding agent works on common engineering tasks.
2. Measure, with a blind and execution-based eval, whether each skill improves outcomes compared with the same agent without the skill.
3. Publish results honestly, including null and negative results.

## 2. Skill format

Each skill lives at `skills/<name>/SKILL.md`:

- YAML frontmatter with `name` and `description`. The description is what an agent sees before loading the skill, so it must state when the skill applies.
- A body of instructions loaded only when the skill is triggered (progressive disclosure).
- Optional supporting files in the same folder, referenced from the body.

Skills must not depend on a specific agent's proprietary features unless that dependency is stated.

## 3. Initial skills

| Skill | Purpose |
|---|---|
| `tdd-first-fix` | Reproduce a bug with a failing test before changing code, then make the minimal fix that turns it green. |
| `pr-babysit` | Drive an open pull request through CI failures and review feedback until it is mergeable. |
| `swarm-review` | Review a change with several independent reviewers in parallel, then reconcile and verify findings. |
| `verify-before-merge` | Run the checks that prove a change works before declaring it done or merging. |
| `investigate` | Establish root cause through evidence and hypothesis testing before modifying code. |

## 4. Blind-eval method

### 4.1 Tasks
- **Held-out.** Eval tasks are not used while writing or tuning a skill.
- **Disguised.** Tasks are phrased as ordinary work requests. They do not name the skill or hint that a particular workflow is being tested.

### 4.2 Ground truth
- **Execution decides.** A trial passes only if the task's hidden checks (tests, scripts, or other executable criteria) pass against the agent's final state.
- LLM judges may be used for supplementary qualitative notes but never decide pass/fail.

### 4.3 Comparison
- **A/B, with-skill vs without-skill.** The same agent, model, task, and environment, differing only in whether the skill is available.
- **Same budget.** Both arms receive identical limits (turns, tokens, wall-clock time, tool access). A skill that only wins by spending more is reported as such.

### 4.4 Trials
- **At least 3 trials per task per arm.** Results report both pass@k (any trial passed) and pass^k (all trials passed) alongside per-trial pass rate.

### 4.5 Guardrails
- **Test edits are an automatic fail.** Any modification, deletion, or skipping of the task's evaluation tests or checks fails the trial, regardless of the final check result.
- **Automatic-fail rule, as enforced (grader rule v2, line-aware).** A patch is disqualified if it:
  - modifies or deletes any existing line of an existing test file, or deletes or renames an existing test file;
  - touches the hidden tests; or
  - adds or edits test configuration (`conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`, `sitecustomize.py`, `usercustomize.py`).

  **Adding tests is allowed**, both new test files and new tests appended to existing files. The hidden tests live outside the agent's workspace and are the ground truth, so added tests cannot change the verdict. Rule v1 disqualified any change under `tests/`, which penalized exactly the test-writing that skills such as `tdd-first-fix` require.

### 4.6 Known confounds
- **Host built-in skills.** The host agent's own built-in skills (for Claude Code, e.g. `verify`, `debug`, `simplify`) are available in both arms. They are present equally, so the comparison stays like-for-like, but they may overlap with the skill under test. This is noted, not removed.

## 5. Reporting and honesty rule

- Every published score states the number of tasks and trials it is based on.
- **Small samples are reported as small samples.** Results from few tasks or trials are labeled as preliminary and are not presented as conclusive.
- Null and negative results are published alongside positive ones.
- No score is published until it has been produced by the harness. Raw run data is kept out of version control (`results/raw/`); published summaries are committed.

## 6. Out of scope for the foundation

- Skill content
- Harness implementation
- Installers

## 7. The 25-skill roadmap

### 7.1 Counting rule
- A skill counts toward the 25 only when it is **written in full and holds a first eval score**.
- Stubs never count.
- The README leaderboard shows each skill's true status: **stub**, **written**, **evaled**, or **proven**.

### 7.2 Wave 1 — Core 5 (skills 1–5)
1. `tdd-first-fix`
2. `pr-babysit`
3. `swarm-review`
4. `verify-before-merge`
5. `investigate`

### 7.3 Wave 2 — Engineering depth (skills 6–15)
6. `bisect-regression`
7. `refactor-safely`
8. `write-tests`
9. `dependency-upgrade`
10. `migration-writer`
11. `perf-hunt`
12. `security-pass`
13. `flaky-test-hunter`
14. `docs-from-code`
15. `release-notes`

### 7.4 Wave 3 — Agent operations (skills 16–25)
16. `eval-writer`
17. `skill-smith`
18. `mcp-server-check`
19. `permission-check`
20. `citation-verifier`
21. `morning-brief`
22. `meeting-followup`
23. `cost-ledger`
24. `handoff-writer`
25. `ship`

### 7.5 Gates
- **Wave 2** writing starts only when the Core 5 are written and skill 1 has a real eval score.
- **Wave 3** starts when Wave 2's first skills are evaled.
- Folders are created wave by wave as skills are written. No empty folders are created ahead of the work.

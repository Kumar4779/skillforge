# SkillForge

SkillForge is a portable library of `SKILL.md` files for coding agents, paired with a blind-eval harness that measures whether each skill actually helps.

**Status:** One skill (`tdd-first-fix`) is written and evaled: a first scored run (v1), a scored re-run after one revision (v2), and a v2 run on a held-out task set are recorded below. The other four planned skills are not yet written.

## What it is

- **Skills.** Each skill is a self-contained `SKILL.md` — YAML frontmatter (`name`, `description`) plus instructions — that an agent loads only when the task calls for it. Skills are meant to be portable across agents such as Claude Code, Cursor, and Codex.
- **Blind-eval harness.** Every skill is tested against held-out tasks it was not written for, with and without the skill, under the same budget. Pass/fail is decided by executing the result, not by asking a model whether it looks right.

A skill earns a place in the library by measurably improving outcomes. If it doesn't, the scorecard will say so.

## Layout

```
skills/      One folder per skill, each containing a SKILL.md
harness/     Blind-eval harness (placeholder)
install/     Installers for supported agents (placeholder)
SPEC.md      Design: initial skills, eval method, reporting rules
LEARNING.md  Concepts checklist
```

## Planned skills

| Skill | Status |
|---|---|
| `tdd-first-fix` | Evaled — eval closed, no lift measured |
| `pr-babysit` | Not yet written |
| `swarm-review` | Not yet written |
| `verify-before-merge` | Not yet written |
| `investigate` | Not yet written |

See [SPEC.md](SPEC.md) for the design and evaluation method.

## Eval results

### `tdd-first-fix` — scored runs

A = no skill, B = with `tdd-first-fix`. Grader rule v2 (line-aware). Same three tasks, prompt, permissions, and timeout in both runs; only the skill text changed between v1 and v2 (see [SPEC.md §8](SPEC.md#8-revision-log)).

- v1: [`harness/results/tdd-first-fix-scored-v1.json`](harness/results/tdd-first-fix-scored-v1.json)
- v2: [`harness/results/tdd-first-fix-scored-v2.json`](harness/results/tdd-first-fix-scored-v2.json)

| Task | v1 A | v1 B | v2 A | v2 B |
|---|---|---|---|---|
| `task-001` | 3/3 | 3/3 | 3/3 | 3/3 |
| `task-002` | 3/3 | 0/3 | 3/3 | 3/3 |
| `task-003` | 3/3 | 3/3 | 3/3 | 3/3 |

| Overall | v1 A | v1 B | v2 A | v2 B |
|---|---|---|---|---|
| Pass rate | 9/9 (100%) | 6/9 (67%) | 9/9 (100%) | 9/9 (100%) |
| Tasks passed in all 3 trials (pass^k) | 3/3 | 2/3 | 3/3 | 3/3 |
| Total cost | $0.9548 | $1.0991 | $0.9028 | $1.1192 |
| Cost per solved task | $0.1061 | $0.1832 | $0.1003 | $0.1244 |

3 tasks x 3 trials per arm. Small sample — directional, not conclusive. Both arms also have the host's built-in skills available.

v2 was revised in response to the v1 `task-002` failures, so `task-002` is not held out for v2.

### Held-out set (tasks 004-006)

Source: [`harness/results/tdd-first-fix-heldout-v1.json`](harness/results/tdd-first-fix-heldout-v1.json). Skill version: commit `e088f61`, SKILL.md sha256 `0f89bd5f5e29` (v2). Grader rule v2 (line-aware). A different task set from the v1/v2 scorecard above; the numbers are not combined.

| Task | A passes | B passes |
|---|---|---|
| `task-004` | 3/3 | 3/3 |
| `task-005` | 3/3 | 3/3 |
| `task-006` | 3/3 | 3/3 |

| Overall | A (no skill) | B (with skill) |
|---|---|---|
| Pass rate | 9/9 (100%) | 9/9 (100%) |
| Tasks passed in all 3 trials (pass^k) | 3/3 | 3/3 |
| Total cost | $0.9370 | $1.1189 |
| Cost per solved task | $0.1041 | $0.1243 |

Held-out set: tasks 004-006 were built after tdd-first-fix v2 was frozen; the skill was never revised against these tasks. 3 tasks x 3 trials per arm. Small sample — directional, not conclusive. Both arms also have the host's built-in skills available.

### Verdict — tdd-first-fix

Eval closed for `tdd-first-fix` v2. Across 10 tasks the no-skill baseline passed 39 of 39 scored and calibration runs, including multi-module tasks with interacting bugs; after the v2 revision the skill arm matched it at roughly 20% higher cost per solved task (+24% on tasks 001-003, +19% on the held-out set). No lift measured. Scope: small, self-contained bug-fix tasks with the current frontier model; long-horizon or ambiguous work and weaker models were not tested. The skill stays published; SkillForge claims no measured benefit for it.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

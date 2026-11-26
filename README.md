# SkillForge

SkillForge is a portable library of `SKILL.md` files for coding agents, paired with a blind-eval harness that measures whether each skill actually helps.

**Status:** Foundation — no skills are written or evaled yet; scores will be published here when they exist.

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
| `tdd-first-fix` | Evaled — first score |
| `pr-babysit` | Not yet written |
| `swarm-review` | Not yet written |
| `verify-before-merge` | Not yet written |
| `investigate` | Not yet written |

See [SPEC.md](SPEC.md) for the design and evaluation method.

## Eval results

### `tdd-first-fix` — first scored run

Source: [`harness/results/tdd-first-fix-scored-v1.json`](harness/results/tdd-first-fix-scored-v1.json). Grader rule v2 (line-aware). A = no skill, B = with `tdd-first-fix`.

| Task | A passes | B passes |
|---|---|---|
| `task-001` | 3/3 | 3/3 |
| `task-002` | 3/3 | 0/3 |
| `task-003` | 3/3 | 3/3 |

| Overall | A (no skill) | B (with skill) |
|---|---|---|
| Pass rate | 9/9 (100%) | 6/9 (67%) |
| Tasks passed in all 3 trials (pass^k) | 3/3 | 2/3 |
| Total cost | $0.9548 | $1.0991 |
| Cost per solved task | $0.1061 | $0.1832 |

3 tasks x 3 trials per arm. Small sample — directional, not conclusive. Both arms also have the host's built-in skills available.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

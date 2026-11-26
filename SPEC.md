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

## 7. The roadmap (about 41 skills)

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

### 7.6 Principles layer (about 10 micro-skills)

One idea per skill, each derived from SkillForge's own eval record and stated in SkillForge's words. Unlocks when Wave 1 is fully written (5 of 5). Seed list:

1. `measure-before-claiming` — say a skill, fix, or change helps only when a measurement shows it; otherwise say it is unmeasured. (The `tdd-first-fix` verdict, §8.)
2. `reproduce-first` — make the failure happen before changing anything; a fix for a failure you never saw is a guess.
3. `calibrate-before-comparing` — measure the baseline alone before running an A/B; a task the baseline always solves cannot show a difference. (Tier-2 and tier-3 calibration, §8.)
4. `publish-the-failure` — report negative and null results with the same prominence as positive ones. (`tdd-first-fix` v1, B 6/9.)
5. `smallest-change-honest-scope` — make the smallest change that fixes the defect, and count a contract-violating side effect as part of the defect, not behaviour to preserve. (The v2 carve-out, §8.)
6. `verify-dont-vote` — agreement between reviewers or runs is not evidence; settle every disputed or top claim by checking the artifact itself.
7. `permissions-before-capability` — declare the access a task needs before using it, and ask before anything outside that declaration. (§9.2a.)
8. `ground-truth-is-execution` — decide pass or fail by running the real thing; a judgment of how the output looks does not decide. (§4.2.)
9. `cost-is-a-result` — report what a result cost next to whether it passed; parity at higher cost is not a gain. (Cost per solved task, §8.)
10. `frozen-artifacts-stay-frozen` — an artifact that has been measured is not edited in place; a change makes a new version with its own measurement. (The `tdd-first-fix` standard exemption, §9.)

### 7.7 Wave 4 — Sensei product skills (6)

Skills for Sensei's daily-life surfaces, following the document-family pattern (§10.1): one skill per output type, with bundled scripts for the deterministic file work. Unlocks when Wave 1 is fully written (5 of 5).

1. `word-documents` — create and edit word-processor documents.
2. `pdf-documents` — read, extract from, fill, and produce PDFs.
3. `spreadsheets` — create, clean, and calculate in spreadsheets.
4. `slide-decks` — build and revise presentations.
5. `research-brief` — gather sources and write a cited brief.
6. `comms-draft` — draft emails, messages, and announcements in the user's voice.

### 7.8 Counting rule for the expanded map

- **Workflow skills** (Waves 1–4) count when written in full **and** holding a first eval score. Stubs never count.
- **Principle skills** do not count toward the total until a method for measuring them exists. A principle is meant to change many decisions across many tasks, and SkillForge has no method yet for measuring that. The method is an open problem, recorded here; it is not solved by assertion.
- **Total map:** 25 (Waves 1–3) + about 10 (Principles layer) + 6 (Wave 4) = **about 41**.
- **Counted today: 1** (`tdd-first-fix`: written, evaled, eval closed). Written but not yet evaled, and so not counted: `pr-babysit`, `swarm-review`.
- Folders for the new families are created when each skill is written, not before (§7.5).

## 8. Revision log

### `tdd-first-fix`

- **v1 scored run** (`harness/results/tdd-first-fix-scored-v1.json`, 3 tasks x 3 trials per arm): A (no skill) 9/9, B (with skill) 6/9. All three B failures were on `task-002`. Mechanism: the smallest-change rule led the agent to keep the existing in-place `values.sort()`, which mutates the caller's list and fails the hidden no-mutation test. All three A runs replaced it with a sorted copy.
- **v2 hypothesis:** carving contract-violating side effects out of the smallest-change rule (and pinning conventional input contracts in the failing test) recovers `task-002` without losing `task-001` or `task-003`.
- **Held-out caveat:** v2 was revised in response to a `task-002` failure, so `task-002` is no longer held out for v2. A v2 gain on `task-002` shows the revision addresses the observed failure; it does not show generalization. That requires tasks not used in the revision.
- **Closure (eval closed, no lift measured).**
  - *v1 negative result:* B 6/9 vs A 9/9 on tasks 001-003. All three B failures were on `task-002`, where the smallest-change rule preserved the caller-mutating in-place sort.
  - *v2 fix and recovery:* carving contract-violating side effects out of the smallest-change rule brought B to 9/9 on tasks 001-003, matching A 9/9 (not held out for `task-002`).
  - *Held-out, no harm:* on tasks 004-006, built after v2 was frozen, A 9/9 and B 9/9.
  - *Calibration ceiling:* the baseline arm alone passed tier-2 (tasks 007-009, cross-module, 9/9) and the tier-3 probe (`task-010`, seven modules, two interacting bugs, 3/3). Under the decision rule registered before the tier-3 run, a 3/3 baseline closes the eval.
  - *Verdict:* across 10 tasks the baseline passed 39 of 39 scored and calibration runs. The v2 skill arm matched it at roughly 20% higher cost per solved task (+24% on tasks 001-003, +19% held-out). No lift measured.
  - *Scope:* small, self-contained bug-fix tasks with the current frontier model. Long-horizon or ambiguous work and weaker models were not tested. The skill stays published; SkillForge claims no measured benefit for it.

## 9. Authoring standard

Patterns below were learned by reading the primary sources listed in §9.4 for structure and method. Each pattern names where it came from. The wording here and in every SkillForge skill is original.

### 9.1 Adopted patterns

1. **Trigger-first description.** The `description` frontmatter is the main thing a host uses to decide whether to load a skill, so it states both what the skill does and the concrete situations that should trigger it, starting with "Use when". Hosts tend to under-trigger skills, so name the situations plainly rather than abstractly. *Learned from:* anthropics/skills `skill-creator` (description as the primary triggering mechanism; making descriptions explicit enough to counter under-triggering); pstack `blast-radius` and `swarm` (descriptions that quote the phrases a user actually types).
2. **Skip conditions in the trigger.** A skill with real cost (extra turns, setup, or risk) says when *not* to use it, in the description where cost warrants it and always in the body's "When to use" not-cases. *Learned from:* pstack `tdd` (its description limits when it runs and names the cases to skip; its body gives a fallback when the skill's method is impractical).
3. **Near-miss negatives in trigger testing.** When a skill's triggering is tested, the should-not-trigger cases are near misses that share vocabulary with the skill, not obviously unrelated requests. *Learned from:* anthropics/skills `skill-creator` (trigger-eval query design).
4. **Progressive disclosure.** Three levels: frontmatter is always in context; the SKILL.md body loads when the skill triggers and stays short (well under 500 lines); bundled files load only when the body points to them, with a sentence saying when to read each. Variant-specific detail (per language, per platform) goes in a separate reference file per variant, so only the relevant one is read. *Learned from:* anthropics/skills `skill-creator` (three-level loading, size guidance, per-variant references) and `mcp-builder` (a lean workflow body that points to phase-specific reference files).
5. **Bundled scripts are black boxes.** Deterministic, repeated work goes in `scripts/`. The skill tells the agent to run the script (with `--help` first) rather than read its source, which keeps the context window clean. A step that agents keep rewriting by hand across runs is a signal to bundle a script. *Learned from:* anthropics/skills `webapp-testing` (run helpers as black boxes) and `skill-creator` (repeated helper code across test runs signals a script to bundle); pstack principle `build-the-lever` (a script a reviewer can rerun beats hand work).
6. **Delegate, don't restate.** A skill that needs another skill's method points to it by name or path instead of copying it. *Learned from:* pstack authoring playbook and `blast-radius` (companion skills referenced, not duplicated).
7. **Guardrail phrasing: short imperatives, a reason where rules collide.** Hard rules are short, direct imperatives. Prose that does not change a decision is cut. Where a rule can conflict with another goal, the rule carries its reason or its carve-out, because a bare rule gets applied past its purpose. SkillForge evidence: `tdd-first-fix` v1's bare "smallest change" rule preserved a harmful side effect; v2's carve-out fixed it (§8). *Learned from:* anthropics/skills `skill-creator` (explain the why; treat all-caps MUSTs as a warning sign); pstack authoring playbook (keep only prose that changes a decision; explain only when a rule is confusing without a reason).
8. **Failure modes as symptom → correction.** Each failure mode names an observable symptom the agent can notice in its own work, then the corrective action. Include the fallback for when the skill's main method cannot be applied. *Learned from:* pstack `tdd` (fallback when a failing test is impractical) and `swarm` (a missing result is a gap, never a pass); anthropics/skills `webapp-testing` (named common pitfall with the do / don't pair).
9. **Evidence-graded reports.** A skill's report states its evidence, not just its conclusion: file and line, the command run and its output, and how far each claim was verified. A claim without evidence is marked unproven or dropped. *Learned from:* pstack `blast-radius` (graded levels of certainty, real `file:line`, never invent a caller), `swarm` (results carry evidence; unproven results are respawned or recorded as gaps), `tdd` (final response reports failing-before and passing-after evidence), and principle `prove-it-works` (verify the real artifact, not a proxy).
10. **Baseline-compared iteration that generalizes.** A skill is tested against a no-skill baseline on the same prompts. Revisions generalize from what failed instead of patching the specific test case. *Learned from:* anthropics/skills `skill-creator` (with-skill and baseline runs side by side; avoid overfitting changes to the examples). SkillForge adds execution grading, held-out tasks, and pre-registered decision rules (§4, §8).

### 9.2 SkillForge extensions

- **(a) Permissions section.** Every skill has a short `## Permissions` section listing the tools and access it needs: for example, read files, edit files in the repo, run the test suite, read a PR, push to a branch, post comments. It also lists anything it must never do without explicit approval. Sensei's permission gates can enforce the section; other hosts can ignore it, since it is ordinary Markdown.
- **(b) Written to be evaled.** Every skill's "Done when" lists checkable behavior: things a grader can observe in the diff, the commands run, the outputs, or the report. "Done when" never says "the code is clean" or "the review is thorough". If a done condition cannot be checked, it is rewritten until it can.

### 9.3 Skill structure

Frontmatter: `name` (lowercase, hyphenated, matching the folder) and a trigger-first `description`. Body sections, in order: **When to use** (with not-cases), **Steps**, **Permissions**, **Guardrails**, **Failure modes**, **Done when**. Bundled files (`scripts/`, `references/`), when present, are each referenced from the body with when to read or run them.

**Exemptions and backfills.** `tdd-first-fix` v2 (commit `e088f61`, SKILL.md sha256 `0f89bd5f5e29`) predates the Permissions-section standard and is intentionally not backfilled, so the closed eval's record (§8) keeps pointing at the exact text that was tested. The section will be added with any future behavioural revision, which will carry its own version and its own eval. `pr-babysit` was backfilled with a Permissions section when the standard was adopted, because it had not been evaled.

### 9.4 Sources and licenses

| Source | What was read | License, as stated in the repo |
|---|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) | `README.md`; `skills/skill-creator/SKILL.md` (skill-creation guidance); `skills/mcp-builder/SKILL.md`; `skills/webapp-testing/SKILL.md`; `skills/pdf/SKILL.md` | No repository-wide license file. The README states that many skills are Apache 2.0, including the document skills. Each skill read ships a `LICENSE.txt` with Apache License 2.0 (checked for `skill-creator`, `mcp-builder`, `pdf`). |
| [backnotprop/pstack](https://github.com/backnotprop/pstack) (a mirror of `cursor/plugins/pstack`) | `README.md`; `docs/guide/08-principles.md`; `skills/poteto-mode/playbooks/authoring-a-skill.md`; `skills/swarm/SKILL.md`; `skills/tdd/SKILL.md`; `skills/blast-radius/SKILL.md`; `skills/principle-prove-it-works/SKILL.md` | MIT (`LICENSE`, "Copyright (c) 2026 Lauren Tan"; README "license: MIT"). |

**Rule:** patterns, structure, and methods are adopted freely. Text is original; no source skill's text is copied into this repository. Any future adaptation of licensed text requires attribution, and the source's license notice where its license calls for one, recorded in a `NOTICE` or `ATTRIBUTION.md` file in that skill's folder.

## 10. Coverage map

Reference catalogs fetched 2026-11-25: [anthropics/skills](https://github.com/anthropics/skills) (19 skills) and [backnotprop/pstack](https://github.com/backnotprop/pstack) (59 skills under `skills/`, of which 24 are `principle-*`, plus 3 automation skills under `automations/benny/`). Entries were classified from each skill's own description.

**Marks**, judged against what SkillForge has written today:

- **Covered** — SkillForge has a written skill for it.
- **Analogue** — a written SkillForge skill works the same territory differently.
- **Gap** — they have it and SkillForge does not. Where a roadmap slot (§7) is planned for the territory, it is named; planned is not written.
- **Not applicable** — specific to their product, brand, or host.

### 10.1 Anthropic skills (19)

| Entry | Mark | SkillForge map |
|---|---|---|
| `docx` | Gap | Wave 4 `word-documents` |
| `pdf` | Gap | Wave 4 `pdf-documents` |
| `pptx` | Gap | Wave 4 `slide-decks` |
| `xlsx` | Gap | Wave 4 `spreadsheets` |
| `doc-coauthoring` | Gap | Wave 4 `word-documents`, `research-brief` |
| `internal-comms` | Gap | Wave 4 `comms-draft`; Wave 3 `meeting-followup` |
| `algorithmic-art` | Gap | Not planned (creative; outside SkillForge's scope) |
| `canvas-design` | Gap | Not planned (creative) |
| `slack-gif-creator` | Gap | Not planned (creative) |
| `theme-factory` | Gap | Not planned (visual styling) |
| `frontend-design` | Gap | Not planned |
| `brand-guidelines` | Not applicable | Anthropic's own brand |
| `web-artifacts-builder` | Not applicable | claude.ai artifacts |
| `claude-api` | Not applicable | Anthropic API reference |
| `academy-guide` | Not applicable | Claude Academy content |
| `mcp-builder` | Gap | Wave 3 `mcp-server-check` (checks servers rather than building them) |
| `webapp-testing` | Gap | Wave 1 `verify-before-merge` (adjacent, not equivalent) |
| `skill-creator` | Gap | Wave 3 `skill-smith`, `eval-writer`. The SkillForge harness does the eval part, but it is a harness, not a skill. |
| `discernment-nudge` | Gap | Principles layer (`measure-before-claiming`) |

Today: 0 Covered, 0 Analogue, 15 Gap (5 of them not planned), 4 Not applicable.

### 10.2 pstack, by family

| Family | Entries | Mark | SkillForge map |
|---|---|---|---|
| Principles layer | the 24 `principle-*` skills, indexed by `poteto-mode` | Gap | Principles layer (§7.6) |
| Review and parallel work | `swarm`, `interrogate` | Analogue | `swarm-review` (multi-pass review with code-verified consolidation) |
| | `arena` | Gap | Not planned |
| Bug fixing | `tdd` | Covered | `tdd-first-fix` |
| PR tending | `poteto-mode` babysit playbook | Covered | `pr-babysit` |
| Understanding code | `how`, `why`, `teach` | Gap | Wave 1 `investigate` (for `why`-style regressions) |
| Change safety | `blast-radius` | Gap | Wave 1 `verify-before-merge` |
| Design and planning | `architect`, `figure-it-out`, `sharpen`, `reframe` | Gap | Not planned |
| Session memory and handoff | `recall`, `ketchup`, `ketchup-video`, `show-me-your-work`, `in-your-own-words`, `bro` | Gap | Wave 3 `handoff-writer` |
| Self-improvement | `reflect`, `automate-me`, `correct` | Gap | Wave 3 `skill-smith` |
| Writing quality | `technical-writing`, `unslop`, `no-comments` | Gap | Wave 2 `docs-from-code` (adjacent) |
| Measurement | `benchmark-checklist` | Gap | Wave 2 `perf-hunt`; Principles `cost-is-a-result` |
| Language-specific | `typescript-best-practices` | Gap | Not planned |
| Verification family | `create-verification-skill`, `maintain-verification-skill`, `create-formal-verification-skill`, `maintain-formal-verification-skill`, `statechart` | Gap | Wave 1 `verify-before-merge` (generic only); project-specific verification is not planned |
| Routing and setup | `poteto-mode` (as a router), `poteto-help`, `setup-pstack` | Not applicable | pstack's own configuration and routing |
| Host-specific | `make-bot-ui` (Grok Bot webhooks); the 3 `automations/benny/` skills (Cursor automations only) | Not applicable | — |

### 10.3 Gaps this map exposed

1. **A principles layer.** pstack's 24 one-idea principle skills give agents a vocabulary that other skills and users can invoke by name. SkillForge has no equivalent.
2. **A product and document skills family.** Anthropic's `docx`, `pdf`, `pptx`, and `xlsx` cover everyday document work. SkillForge's map was coding-only.

Both are added to the roadmap in §7.6 and §7.7.

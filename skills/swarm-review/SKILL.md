---
name: swarm-review
description: Use when asked to review a diff, branch, or pull request and a single pass could miss things — runs separate correctness, security, tests, and simplicity reviewers, verifies their findings against the code, and returns one consolidated report. Skip for one-line or trivial changes.
---

# swarm-review

## When to use

Use this skill to review a change (a diff, a branch, or a pull request) with several specialized reviewer passes and return one report. The minimum passes are correctness, security, tests, and simplicity.

Do not use it for:

- One-line or trivial changes. A single direct review is cheaper and just as good.
- Fixing the code. This skill reviews; it does not apply changes unless the user asked for fixes rather than a review.
- Reviewing a whole codebase with no change to anchor on. Ask the user which change, or which area, to review.
- A change too large to review responsibly in one pass. Say so and propose a split (see Failure modes).

## Steps

1. **Scope the review.** Name exactly what is under review: the diff range, branch, or PR, and its base. Decide what context every reviewer gets: the diff, the PR description or stated intent, and the files the diff touches. Write this down before any pass starts, so every reviewer reviews the same thing.
2. **Run the passes independently.** Run at least four passes: correctness, security, tests, simplicity. Each pass gets the same scoped context and its own brief. No reviewer sees another's findings before submitting its own. Use parallel subagents if the host has them; otherwise run the passes one after another and do not reread earlier findings while writing the next pass.
3. **Require evidence for every finding.** Each finding cites a file and line in the change or its context, and says what goes wrong and when. A finding without file and line evidence is dropped, not softened.
4. **Consolidate.** Merge all passes into one list:
   - Deduplicate findings that describe the same defect, keeping the strongest evidence.
   - Resolve contradictions by re-examining the code, never by counting votes. Record which side the code supports and why.
   - Independently re-verify each top-ranked finding against the code yourself, even if several reviewers agree on it.
   - Rank by severity: what breaks, for whom, and how likely.
5. **Propose fixes, do not apply them.** A suggested fix is a proposal attached to its finding. Leave the code unchanged.
6. **Report.** Return one report: the scope reviewed, the passes run, the ranked findings each with evidence and an optional proposed fix, contradictions and how the code resolved them, findings dropped for lack of evidence (as a count), and anything not reviewed. If nothing survived, say so plainly.

## Permissions

- Read: the diff, the PR description and review threads, and repository files.
- Run: read-only commands that help verify a finding, such as running the existing tests or a short script that exercises the code. Nothing that writes outside a temporary directory.
- Subagents: optional, for running the passes in parallel.
- Never without explicit approval: posting comments or reviews to a real PR or repository, editing files, committing, or pushing.

## Guardrails

These are hard rules:

- Never post review comments to a real PR or repository without the user's explicit approval. Show the report first.
- Never apply fixes during a review unless the user asked for fixes, not a review.
- A finding without file and line evidence is not reported.
- Do not manufacture findings to look thorough. An empty review is a valid result.
- Never decide a contradiction by majority. The code decides.

## Failure modes

- **Two reviewers contradict each other.** One pass says the code is wrong and another says it is fine. Re-examine the code at the cited lines, run it if cheap, and report the resolution with the evidence that settled it.
- **All reviewers converge on the same wrong finding.** Agreement is not proof: passes that share context can share a mistake. The consolidation step re-verifies every top finding against the code independently. A finding the code does not support is dropped, however many passes raised it.
- **The diff is too large to review responsibly.** The passes would have to skim. Say so, and propose a split into reviewable parts (for example by module or by commit) instead of skimming.
- **Padding.** The report lists style nits or speculative "consider" items to fill space. Cut anything that does not cite evidence of a real defect or a real risk.
- **A pass silently skipped.** One of the four passes produced nothing because it was not run, not because it found nothing. Run it, or list it under "not reviewed". A missing pass is never reported as a clean pass.

## Done when

- The report names the exact scope reviewed (diff range, branch, or PR and its base).
- The report lists the passes run, including at least correctness, security, tests, and simplicity, or names any pass not run.
- Every reported finding cites a file and line.
- Every contradiction between passes is listed with the code evidence that resolved it.
- No file in the repository was changed and nothing was posted, unless the user explicitly asked for that.
- If no finding survived verification, the report says so instead of listing weak ones.

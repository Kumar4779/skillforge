---
name: pr-babysit
description: Use when asked to get an open pull request merge-ready, or to keep tending one through CI failures, review comments, and merge conflicts.
---

# pr-babysit

## When to use

Use this skill to tend an open pull request until it is merge-ready: CI is green, every review thread is addressed, and the branch merges cleanly. The PR's intent does not change.

Do not use it for:

- Writing the PR's feature or fix from scratch. That is the PR author's work, not tending.
- Merging. Merge only if the user explicitly asks.
- A PR whose purpose is unclear. Ask the user what the PR is meant to do before changing anything.
- A PR you cannot push to. Report the blockers and the fixes you would make instead.

## Steps

1. **Read the full PR state first.** Read the description, the diff, CI status, and every review thread, including resolved ones. Before touching anything, state what "merge-ready" requires for this PR: which checks must pass, which approvals are needed, and whether the base branch has moved.
2. **Classify every blocker.** Put each one in exactly one class: CI failure, review request, merge conflict, or waiting on humans (approvals, answers, decisions only someone else can make).
3. **Fix CI failures at the cause.** Reproduce each failure locally, find the cause, and fix it. Push, then re-check CI. A green re-run of a failure you did not fix is not a fix.
4. **Address every review thread.** Each thread gets either a change or a written reply that explains why not. Never silently ignore a thread.
5. **Resolve conflicts.** Merge or rebase onto the base branch as the repo's convention requires, and resolve conflicts preserving both sides' intent. Note any file the resolution changed that the PR did not originally touch.
6. **Loop.** After each push, re-read CI and the review threads, because new failures and new comments arrive. Repeat steps 2–5 until CI is green and nothing is blocked except on humans.
7. **Report.** State what was blocking, what you changed for each blocker, what you replied on each thread, any files touched outside the original diff, anything still waiting on humans, and the final CI status.

## Permissions

- Read: the PR description, diff, CI status and logs, and review threads.
- Run: the project's test and CI commands locally, and git commands to fetch, commit, and push to the PR branch.
- Subagents: none required.
- Never without explicit approval: merging the PR, force-pushing, resolving a review thread without a change or a written explanation, or posting replies beyond the review threads being addressed.

## Guardrails

These are hard rules:

- Never merge the PR unless the user explicitly asked you to.
- Never resolve a review thread without a change or a written explanation.
- Never force-push a branch others may be using. If history must be rewritten, ask first.
- Never edit tests to make CI pass. A test that is genuinely wrong is reported to the user, not quietly changed.
- Do not expand the PR's scope with unrelated changes, however tempting.
- If a CI failure looks unrelated or flaky, re-run it once. If it passes inconsistently, report it as suspected-flaky with evidence (job names, run links, the failing and passing outputs) instead of papering over it.

## Failure modes

- **A reviewer request contradicts the PR's stated purpose.** Reply on the thread asking for clarification and quoting the stated purpose. Do not silently comply, and do not silently refuse.
- **CI fails on something outside the PR's diff.** Report it as a blocker with evidence. Fix it only if the fix is trivial and clearly correct; otherwise leave it for the user.
- **Re-running until green.** A failure went away on re-run and you moved on. That is papering over. Re-run once at most, then fix the cause or report it as suspected-flaky.
- **A conflict resolution rewrites someone else's change.** You resolved a conflict by dropping the base branch's side. Redo it so both sides' intent survives, and note the files involved.
- **Declaring merge-ready while threads are open.** CI is green but a review thread has no change and no reply. The PR is not merge-ready until every thread is addressed.

## Done when

- CI is green on the latest push, or every remaining failure is reported as suspected-flaky or out-of-diff with evidence.
- Every review thread has a change or a written reply.
- The branch merges cleanly with the base branch, and any file touched outside the original diff is noted.
- Anything still waiting on humans is listed.
- The report covers each blocker, what was done about it, and the final CI status.

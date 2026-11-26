---
name: tdd-first-fix
description: Use when fixing a bug, regression, or GitHub issue in a codebase that has a test suite.
---

# tdd-first-fix

## When to use

Use this skill for bug fixes, regressions, and issue reports in a codebase with a working test suite.

Do not use it for:

- Docs-only or config-only changes.
- A repo with no test framework. In that case, say plainly that the repo has no test framework and stop. Do not fake TDD.

## Steps

1. **Reproduce.** Read the issue and reproduce the failure before changing anything.
2. **Write one test.** Write ONE new test that captures the bug: the smallest test that fails for the right reason. Where the function's contract on its inputs is conventional, pin it in the same test (for example, inputs are unchanged after the call).
3. **Confirm it fails correctly.** Run the new test and confirm it fails for the expected reason, not because of a typo, import error, or broken setup.
4. **Make the smallest fix.** Make the smallest code change that fixes the bug. A side effect of the existing code that violates the function's contract (for example, mutating an argument the caller reasonably expects to keep) is part of the defect, not behavior to preserve for minimality's sake.
5. **Confirm it passes.** Run the new test. It must pass.
6. **Check for regressions.** Run the affected module's existing tests. There must be no regressions.
7. **Report.** State the test you wrote, the change you made, and the actual test results.

## Guardrails

These are hard rules:

- Never edit the new test after step 3 to make it pass.
- Never edit existing tests.
- Make the smallest change that fixes the bug. No unrelated refactors. Removing a contract-violating side effect, such as mutating the caller's argument, is part of the fix, not a refactor.
- Never touch files outside the repo.
- If you cannot reproduce the bug, stop and report that. Do not guess a fix.

## Failure modes

- **The test passes immediately.** It does not capture the bug. Rewrite the test.
- **The test fails for the wrong reason.** Fix the test setup, not the code.
- **The fix breaks other tests.** The change is wrong or too broad. Narrow it.
- **No test framework exists.** Stop and report.
- **Preserving a harmful side effect for minimality.** You kept an in-place mutation because removing it felt like a bigger change. It is part of the defect. Remove it.

## Done when

- The new test failed before the change and passes after it.
- The affected test suite is green.
- The report lists the test, the change, and the results.

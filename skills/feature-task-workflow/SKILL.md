---
name: feature-task-workflow
description: Use for Feature task lifecycle. Enforce four-stage owner-led workflow through an open PR.
---

# Feature task workflow

This standard governs the Feature task lifecycle and leader coordination of agents. It ends at PR handoff, not PR acceptance, merge, release, or deployment. Follow applicable repository Git/PR rules and CI/CD processes separately.

A Feature has exactly four stages, in order:

1. Analysis (`analisy`)
2. Development / TDD (`developer`)
3. Review (`reviewer`)
4. Integration Test (UAT) (`tester`)

Do not skip, reorder, or add lifecycle stages. Agents may coordinate within a stage; the Owner decides requirements, acceptance criteria, and any waiver.

## 1. Analysis

Use `DEVPOD_WORKSPACE_ID` as the task number and DevPod workspace ID. Read it from the environment; do not guess or substitute another identifier. If unset or empty, ask the Owner before proceeding. The Owner provides `./docs/${DEVPOD_WORKSPACE_ID}/story.md` as the initial discussion guide. Read this file as input, not as agent-authored content: agents may read it but must not edit, overwrite, or delete it. Discuss its contents with the Owner, clarify requirements, and agree on the plan before implementation. Create both documents in that directory before development:

- PRD document
- UAT document.

Record agreed acceptance criteria and required integration tests in the UAT. Resolve ambiguity with the Owner rather than inventing requirements.

## 2. Development / TDD

The `developer` implements the agreed feature. Use vibe coding with TDD by default; use manual coding only when the Owner explicitly selects it. Create and run relevant unit tests. Follow project conventions and applicable Odoo development/security/testing guidance. Do not expand scope without Owner agreement.

## 3. Review

The `reviewer` reviews the resulting changes. Report actionable findings and their disposition. A review does not replace tests or UAT.

## 4. Integration Test (UAT)

The `tester` must:

- Create Python automation integration tests for the agreed UAT criteria.
- Prepare the required automation environment safely.
- Run the integration tests as UAT against the agreed criteria.
- Record decisions, artifacts, actual results, and evidence on the Feature issue/task.
- Preserve failures. If integration tests fail, the tester may create or identify unit tests to help the developer continue TDD; then rerun the applicable workflow checks.

### Decision and PR gate

The stage-4 decision document is exactly one of `ACCEPT` or `ACCEPTED_WITH_WAIVER`.

- Normal path: issue `ACCEPT` only when every required integration test passes.
- Waiver path: a deviation (failed or unrun required test) may be accepted only by the Owner's explicit decision. Record `ACCEPTED_WITH_WAIVER`, list each waived item, retain its actual status (`FAIL`, `NOT RUN`, or other), and record reason, scope, and a separate follow-up Feature task for each item. Waiver does not require updating PRD/UAT.
- A waiver changes the Feature gate only; it is not evidence of a passing test. It does not mean the PR is accepted or merged, or that release or deployment occurred.
- Both paths require opening a PR and recording its link and the UAT decision/results. The handoff is complete only when stage 4 is complete and the PR is open.

Do not claim all delivery is complete when waived follow-up work remains. Set final status to reflect actual results and outstanding tasks. An open PR is not acceptance or merge. PR acceptance, merge, release, and deployment are separate processes; deployment follows applicable CI/CD.

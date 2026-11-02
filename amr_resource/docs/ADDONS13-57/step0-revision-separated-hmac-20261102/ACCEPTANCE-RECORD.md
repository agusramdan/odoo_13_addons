# Acceptance and authorization record — ADDONS13-57 Step 0

Recorded: 2026-11-02T15:37:44+08:00 (Asia/Shanghai)
Owner direction: “prd dan uat approve; lakukan commit dan push; step 0 done ; lanjutkan step 1-4”. The approval refers to the exact PRD/UAT versions and hashes listed below, which were presented immediately before this direction.

## Accepted artifacts

- PRD-DRAFT.md SHA-256: d4bcac54420e0759a40dd0dac59ce827da3a967f45e76b2524454cee1bc31738
- UAT-DRAFT.md SHA-256: 2044fd5e814ae827606701050f86489c14602489e603a55706fa47ec2be47a89
- REVISION-NOTE.md SHA-256: a6f3fa1a7ecdcb837a31d0486b2a118b26ed56e8f4f16e28db4b691926bd065c
- SHA256SUMS.txt verifies the three hashes above.

The four files above are copied byte-for-byte from the externally reviewed set. Their DRAFT labels are preserved; this separate record binds Owner acceptance to their exact bytes. No accepted artifact was edited to record acceptance.

## Scope and gates

- Step 0 is accepted/done for the revised PRD/UAT above, with source baseline `98c608f395add60a2e57182726e077167a01d5a5`.
- Development Steps 1–4 are authorized within the ADDONS13-57 task and its single-addon scope. Commit/push is authorized to the existing feature branch; no force-push, merge, PR acceptance, deployment, production DB access, migration apply, or cutover is authorized by this record.
- HMAC/key-provider implementation is assigned to a separate addon; `amr_resource_hmac` is provisional. ADDONS13-58 is a proposed receiving/dependency task, not accepted scope. Its exact PRD/UAT and the HMAC API/compatibility contract remain a prerequisite for implementing or formally testing that integration.
- The base addon must operate without the HMAC addon for ordinary install/runtime. Apply/destructive cleanup must fail closed before mutation if compatible verification is absent. No unsigned SHA fallback.
- UAT U01–U25 remain NOT RUN. Step 3 cannot begin until Step 2 is accepted and an authorized disposable QA target is prepared. Step 4 requires candidate-specific Owner PR_ACCEPT and verified merge readback.
- Existing worktree/source changes are not accepted by this Step 0 record; implementation, review, and UAT verdicts remain candidate-specific.

# ADDONS13-64 — Git-only rebase report

**Verdict: PASS for authorized local Git rebase and Git verification only.** No implementation, manual commit, push, fetch, tests/runtime, Plane, PR, or acceptance-gate execution. Analyst drafts and STEP0-REPORT.md were not edited. New candidate requires separate document rebinding/acceptance by Lead/Analis.

## Exact candidate identity

| Item | SHA |
|---|---|
| Before ADDONS13-64 | `eaf2c7f016ad9c0ae7945528529e0b73727bed4c` |
| After ADDONS13-64 | `3774c6fda99aab9b5f3d03241a4a876d1cb493b1` |
| Pinned target origin/main | `ac1bcbd66261b92c10078f2a8744a657a3b6490c` |
| Old merge-base | `5de9a5776aecf8383ce580ed0446ee470f1c5425` |

Worktree: `/home/ubuntu/worktrees/ADDONS13-64`.

`git ls-remote --exit-code origin refs/heads/main` immediately before operation returned exactly `ac1bcbd66261b92c10078f2a8744a657a3b6490c refs/heads/main`, matching the local remote-tracking ref. Guards verified exact branch/old HEAD, clean status including untracked files, expected merge-base and eight feature commits, no active rebase/merge/cherry-pick/revert markers, and unchanged pre-operation snapshots. Incoming four paths and feature 32 paths had no overlap. Rebase-related/hook-path Git config lookup returned no configured overrides.

Executed only the authorized history operation:

```sh
git rebase --onto ac1bcbd66261b92c10078f2a8744a657a3b6490c 5de9a5776aecf8383ce580ed0446ee470f1c5425 ADDONS13-64
```

Exit 0; all eight commits replayed successfully. No conflict, resolution, skip, abort, reset, or manual commit.

## Read-back verification

- Target is ancestor of new HEAD: exit 0.
- `git rev-list --count ac1bcbd66261b92c10078f2a8744a657a3b6490c..HEAD`: **8**.
- Range-diff: **eight equivalent (`=`) patches**, no additions/deletions/substantive changes.
- Changed paths relative to target: **32**, exact same path set as before relative to old base.
- `amr_resource/` changed paths relative to target: **0**.
- `git diff --check ac1bcbd66261b92c10078f2a8744a657a3b6490c..HEAD`: exit **0**, empty stdout/stderr. This is whitespace verification, not tests/runtime.
- `git status --porcelain=v1 -z --untracked-files=all`: empty; target feature worktree clean.
- All five non-feature local branch refs unchanged; every other worktree HEAD/branch/status/staged-diff hash/unstaged-diff hash/dirty-file identity unchanged. Worktree membership unchanged.
- Local `origin/main` unchanged at pinned target; no remote write.

### Exact range-diff

```text
1:  0cf31b5 = 1:  ee74d3a feat: add Sentry config and reporting policy
2:  378729c = 2:  c45eb2a feat: make service reporting optional and best-effort
3:  8c09b7c = 3:  ce2804a feat: bootstrap optional Sentry addon and move dependencies
4:  07f5fdc = 4:  26b8ab0 feat: wire Sentry reporter into service client
5:  5912a3b = 5:  d991909 refactor: remove legacy global Sentry settings
6:  397dc6d = 6:  169aa31 docs: document optional Sentry configuration
7:  ab7c545 = 7:  fc111ee fix: import sentry service under Odoo addon namespace
8:  eaf2c7f = 8:  3774c6f fix: keep Sentry tests out of addon imports
```

### Non-feature refs: before = after

| Ref | Unchanged SHA |
|---|---|
| ADDONS13-65 | `24a2824837cff80a08bdb32f40d89fd20eb7ec96` |
| ADDONS13-65-PR | `44302edbdc2a2c4c3509a09321028f64302e66f9` |
| ADDONS13-67 | `61140b3b75b9186771e32a9cd107095d6fbe754e` |
| ODOO13-SKILLS13 | `7449debb1ee2b9780e3f8568c813be0b772cfa5e` |
| main | `c08b050cfd85ccc5c705eb92852e57626eb82806` |

Detached sibling `ADDONS13-65-rev03-implementation` stayed at `a1ce446dc7f7bbcc55d2dcf0a6d36cee9d0009f4`; its two dirty amr_resource files and their diff/content hashes are unchanged. ADDONS13-65 retained exactly `AD skills/UPSTREAM-SOURCE.txt`, including identical staged/unstaged hashes and absent working-tree file. No sibling content/ref was changed by this operation.

## Outside-repository evidence and recovery

All artifacts below are in `/home/ubuntu/docs/ADDONS13-64/step0-reanalysis-20261030/`:

- `REBASE-BEFORE.json`: all local heads, all seven worktrees and pre-operation status/diff/content identity, original path sets.
- `REBASE-EVIDENCE.json`: exact before/after/target/base, post-operation snapshots, range-diff, paths, and ten passing verification assertions.
- `REBASE-RANGE-DIFF.txt`: raw range-diff output.
- `REBASE-EXECUTION.json`: exact operation argv, exit, stdout/stderr.
- `REBASE-REMOTE-BEFORE.txt`: live target remote-ref readback immediately before operation.
- `REBASE-CONFLICTS.json`: no active rebase and no conflicted paths after success.
- `ADDONS13-64-before-rebase.bundle`: complete-history recovery bundle for original feature and pinned origin/main; `git bundle verify` passed before operation. No backup branch/ref was created. Recovery/reset is not authorized by this report.
- `git_rebase_audit.py`: Git-only read/snapshot helper, outside repository.
- `REBASE-REPORT.md`: this report.

**Remaining boundary:** stop here. No tests/runtime or dependency verification were authorized or performed. Prior runtime blockers and acceptance states are not changed by a Git-only PASS.

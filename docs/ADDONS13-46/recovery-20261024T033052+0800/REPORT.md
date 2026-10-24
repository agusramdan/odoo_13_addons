# ADDONS13-46 — Step 1 recovery / finding reconciliation

Mode: VIBE_CODING. Scope: amr_resource only; this directory contains local, untracked evidence, not product changes. This is Developer factual triage, NOT an independent Step 2 review, security verdict, risk acceptance, or gate PASS.

## Candidate and preflight

- Start: 2026-10-24T03:30:52+08:00. Work stopped early after completing Step 1 factual triage and the final offline rerun, within the bounded eight-hour window.
- Worktree: /home/ubuntu/worktrees/ADDONS13-46-dev.
- Branch and exact HEAD: ADDONS13-46 / c177742c25948fe7cbaad4a9b52f9b3b465849d7.
- Tree: 904cb19421e3eeb6ba1006767430ef61d2367deb.
- Merge base: dae519f29e9c4709dc04796b38148b00d333c58b.
- Origin: https://github.com/agusramdan/odoo_13_addons.git.
- Initial and final remote task ref: c177742c25948fe7cbaad4a9b52f9b3b465849d7.
- Initial and final remote main: dae519f29e9c4709dc04796b38148b00d333c58b. Local Git refs and tracked bytes remained unchanged.
- Initial staged/unstaged changes: none. Initial untracked paths: exactly the three protected STEP1 files. Their SHA-256 hashes are in candidate-snapshot.json and matched again during final verification; none was deleted, overwritten, staged, or committed.
- Process preflight used ps -eo pid,ppid,lstart,args. Only this Developer CLI invocation was visible; no competing Developer invocation was identified. Gateway and app-server services are not treated as another active Developer.
- Read-only Git inspection included status --porcelain=v1, branch --show-current, rev-parse HEAD, remote -v, ls-remote origin refs/heads/ADDONS13-46 refs/heads/main, log -3 --format=fuller, merge-base HEAD origin/main, diff --cached --name-status, diff --name-status, worktree list --porcelain, and ls-tree -r --name-only HEAD.
- Existing candidate author/committer is Bot Agus <bot@agusramdan.web.id>. No Git config was changed, and no commit identity override was needed because no commit was permitted.

## 1. Implementation reviewer HIGH: context company/issuer defaults

Disposition from Developer triage: the alleged default_company_id/default_issuer_id authorization bypass is NOT established by the complete source call path. No speculative implementation patch or manufactured RED test was made. The historical reviewer FAIL remains historical FAIL and requires fresh independent reviewer disposition; this report does not convert it to PASS.

### Candidate inheritance and dispatch

amr_resource/models/trust_registry.py declares RegistryAccess as abstract model amr.resource.registry.access (94–96). Issuer (165–169), audience (387–391), and binding (420–424) inherit it through Odoo _inherit, not Python subclass syntax alone. models/__init__.py:7 imports this declaration. The addon also extends base in models/res_users.py:11–23, but that extension defines only user_machine_sudo, not create/check_access_rule.

Upstream Odoo 13 BaseModel._build_model, models.py:477–592, constructs the registry class bases from the declaration, each _inherit registry class, and implicit base (529–571). Therefore, for the declared candidate models, create method resolution is:

- Issuer declaration AmrResourceIssuer.create (289–302) → super → RegistryAccess.create (131–139) → inherited base/core create.
- Audience and binding have no own create override → RegistryAccess.create → inherited base/core create.
- The core later invokes records.check_access_rule dynamically on those model records; this reaches RegistryAccess.check_access_rule (115–119), not just the core implementation.

This is source-level tracing of Odoo's actual registry-class construction algorithm. No installed registry, effective deployed MRO, target addon combination, database, or runtime was started or certified. A different deployed base override that does not cooperate with super would require its own evidence; none is demonstrated by the reported finding.

### Complete create/default/access path

1. RegistryAccess.create explicitly checks create rights, guards supplied company/issuer values, and delegates through super (133–136). It never calls sudo or changes the effective company/user for the create.
2. Core BaseModel.create checks create rights (3754–3755), then calls _add_missing_default_values for each vals entry (3767–3769). That helper calls default_get and merges explicit values over defaults (1764–1808). default_get reads context default_<field> first (1216–1240). Thus the reviewer correctly identified that defaults are added after the early candidate guard; this observation alone is not an authorization exploit.
3. Core create calls _create (3824–3825). _create inserts/caches records, marks dependent fields to compute with records.modified(self._fields, create=True) (3973–3977), validates stored-field constraints, then calls records.check_access_rule('create') before returning (3997–4012).
4. RegistryAccess.check_access_rule calls super, then rejects any record whose company_id differs from self.env.company when not self.env.su (115–119). A normal RPC context is not a sudo environment. Either the core rule or the candidate's effective-company check can reject; a successful return from the initial guard does not skip this later check.
5. Issuer company_id is a stored required Many2one (196–197). A foreign default_company_id therefore produces a foreign company on the resulting issuer and is rejected before create returns. No method in this call path catches that AccessError and returns a supposedly successful record. Under normal RPC transaction handling the exception is not a successful committed creation; this is not a claim about arbitrary trusted server code catching errors and committing its own transaction.

### Stored related child company

Audience company_id (395) and binding company_id (429) are related='issuer_id.company_id', store=True, readonly=True. They are not independent company selections.

- Core fields.py:477–501 derives the related dependency and compute method; readonly means there is no related inverse here.
- Core models.py:3800–3802 protects non-readonly computed fields against recomputation. These child company fields are readonly, so supplying a default_company_id does not get that protection.
- _create marks dependencies on creation (3977); modified queues stored computed fields (5833–5879).
- Reading a queued computed field executes computation before returning its cached value, fields.py:1024–1038. The related computation follows issuer_id.company_id (538–581).
- Related computation defaults to compute_sudo, fields.py:364–370 and 1130–1147. That permits computing the actual parent's company; it does not turn the original recordset's later access check into sudo. A constraint/access exception raised earlier is also denial, not a bypass.

Consequently, default_issuer_id selecting a foreign parent gives the child that foreign company when the access path reads company_id. Adding a spoofed local default_company_id does not make the related company permanently local. The reported path does not explain how the subsequent dynamic company check could be avoided. No demonstrated gap remains to fix within this finding. Native regression execution of these cases remains an explicit QA follow-up, not offline proof of ORM behavior.

### Core source provenance

Read-only upstream retrieval resolved Odoo branch 13.0 to 4cc086d330b73514fbc64a7fcf22d8a7a9f1b691. Exact immutable source URLs and SHA-256 are in upstream-source.json. Sources were fetched into Developer scratch, without importing/running Odoo:

- https://raw.githubusercontent.com/odoo/odoo/4cc086d330b73514fbc64a7fcf22d8a7a9f1b691/odoo/models.py
- https://raw.githubusercontent.com/odoo/odoo/4cc086d330b73514fbc64a7fcf22d8a7a9f1b691/odoo/fields.py

This upstream source identity is not a verified installed target Odoo SHA.

## 2. Test reviewer identity blocker

Current read-only commands independently confirm the exact requested HEAD, branch, merge base, task remote, origin URL, and clean tracked state listed above. The historical test-review transcript itself displays matching HEAD/candidate/base, but its compound terminal invocation exits 1. That exit status alone does not establish a Git identity mismatch. The new Developer result does not repeat the alleged identity mismatch as a current blocker.

Historical raw evidence remains untouched:

/home/ubuntu/.hermes/cache/delegation/live/deleg_846b1aee/task-1.log

Its previous verdict is not rewritten. Current identity verification does not retroactively certify its review coverage or issue a new gate verdict.

## 3. Documentation reviewer missing-source claims

All 56 inline source-file/range references in amr_resource/README.md and amr_resource/docs/*.md were checked against candidate files; zero missing files or invalid line ranges. See source-reference-check.json for every occurrence.

In particular, candidate Git tree and actual contents include:

- amr_resource/models/trust_registry.py: registry models, access guards, source audit, explicit migration, exact runtime lookup.
- amr_resource/models/ir_http.py:41–56 token authentication and change-only metadata; 66–76 session → bearer → params without invalid-bearer fallback.
- amr_resource/models/res_users.py:45–52 principal-bound decode; 76–90 verified context provenance; 11–23 with_user instead of an implicit sudo call.
- amr_resource/transport.py:85–125 bounded public DNS selection; 163–185 pinned socket/TLS; 212–257 bounded HTTPS JSON with no redirect/retry path.

The short citations models/... and transport.py in addon guides are addon-root-relative. A file need not appear in a changed-path listing to exist in the candidate tree. No genuinely broken reference among these claims was found, so existing product documentation and accepted PRD/UAT snapshots were not edited. Checking citation existence/ranges is not certification of every documentation assertion or independent review completeness.

Historical documentation and implementation reviewer transcripts also remain untouched; their hashes and paths are in candidate-snapshot.json. These available raw logs contain truncated tool/result summaries; no missing raw verdict text was reconstructed or replaced.

## 4. Exact comparable offline execution

Python: 3.7.9, verified with the same image's python -B --version.
Image: addons13-34-py379-requirements:local.
Image ID: sha256:d845e4b953894f20b8f30959a297474fc4406fa6317813c041fb1df77a5b8688.

Exact command, unchanged:

```text
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges -e PYTHONDONTWRITEBYTECODE=1 -v /home/ubuntu/worktrees/ADDONS13-46-dev:/src:ro -w /src --entrypoint python addons13-34-py379-requirements:local -B -m unittest discover -s amr_resource/tests -p 'test_*_unit.py'
```

First recovery run: 74 passing, 0 failures, 0 errors, 0 skipped; unittest runtime 1.073 seconds, wall 1.715647507997346 seconds, exit 0. Raw output: offline-suite.log; command/metadata: offline-run.json.

Final comparable run on exact unchanged HEAD c177742c25948fe7cbaad4a9b52f9b3b465849d7:

```text
..........................................................................
----------------------------------------------------------------------
Ran 74 tests in 0.978s

OK
```

74 passing, 0 failures, 0 errors, 0 skipped; wall 1.6077351749991067 seconds; exit 0. Raw output: offline-suite-final.log; command/counts/timing/identity: RESULT.json. The runner asserted every progress character was a pass dot, final OK, and zero exit. All tracked file hashes and Git refs were compared before/after the final run and remained identical.

Offline stubs do not implement the complete Odoo create/default/recompute pipeline. This success is unit-suite evidence, not a runtime reproduction of the proposed bypass, native ACL/MRO installation evidence, or a replacement for QA.

## 5. Recovery decision and handoff to Lead

Step 1 factual recovery is complete with NO product changes. Candidate identity remains c177742c25948fe7cbaad4a9b52f9b3b465849d7; there is no new source candidate SHA to invent. No unrelated tests or count padding were introduced.

The final pass count equals the verified prior 74; it is NOT strictly greater. Therefore commit_permitted=false: no staging, task-branch commit, push, one-shot commit configuration, or post-commit run was performed. Commit-specific staged allowlist/secret gates are not represented as executed. The only new worktree content is this untracked recovery evidence directory, alongside the three original protected untracked files.

For Lead: source is stable for a fresh unified Step 2 (manual code review + security + Semgrep), with this finding reconciliation attached. Developer did not perform or claim that gate. Do not reuse historical FAIL/BLOCKED/NOT RUN as PASS. If the independent reviewer still identifies a concrete exploit, it must include the full post-create/recompute path and return to Step 1 for a tight failing test before any minimal behavior fix.

Remaining gates/prerequisites: independent unified Step 2 disposition; target-specific authorized QA/database preflight before native Odoo/UAT; explicit Owner PR_ACCEPT before any later PR acceptance/merge flow. No target Odoo/DB execution, UAT, Plane mutation, PR creation, merge, deployment, or production action occurred.

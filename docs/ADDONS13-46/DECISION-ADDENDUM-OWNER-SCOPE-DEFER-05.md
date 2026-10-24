ADDONS13-46 — DECISION ADDENDUM OWNER SCOPE DEFER 05 — DRAFT

status=DRAFT; acceptance=false; fresh_lead_review=PENDING
step0_gate=PENDING_LEAD_REVIEW; step1_reassessment=PENDING; Step 2–4=PENDING
DB/QA/runtime/apply/cutover/prod: NOT AUTHORIZED / NOT RUN.

Companions: [PRD](PRD-DRAFT.md), [UAT](UAT-DRAFT.md), [register](RISK-DECISION-REGISTER.md), [revision note](REVISION-NOTE.md), [RESULT](RESULT.json), [SHA256SUMS](SHA256SUMS.txt).

1. Exact provenance O-06

Sumber adalah keputusan Owner yang disampaikan langsung dalam user task ini. Exact quote:
“Lead untuk masalah migrasi tidak terlalu dikhawatirkan. Saat ini code belum masuk production. Issue itu bisa dimasukan dalam task Feature terpisah. Jadi bisa lanjutkan ke step 2-4.”

Tidak ada timestamp/message ID/sender metadata tambahan tersedia; tidak dikarang. Nama waktu direktori berasal dari path revisi yang diminta, bukan timestamp pesan Owner. Tidak mengubah actual DB contents atau memverifikasi status production. Alasan not-in-production/not-too-worried tidak sama dengan residual-risk acceptance atau bukti migrasi aman.

O-06 — OWNER_SCOPE_DEFERRAL_RECORDED: migration-specific completion DEFERRED_TO_FEATURE ADDONS13-57. Scope decision mengizinkan kelanjutan serial ADDONS13-46 setelah fresh Lead review/reassessment; bukan penerimaan snapshot hash baru, Step 1, Step 2, UAT, Owner PR gate, risk waiver, authorization DB/QA/runtime/apply/cutover/prod atau implementation target Feature. Tidak memakai FORCE_DONE_ANALISIS, tidak memberikan blanket skip, tidak mengedit raw NOT_PASS.

Source: ADDONS13-46 UUID 0932b9ca-60ee-44b7-8c88-3e98a173b15b.
Target: ADDONS13-57 UUID 1832b1d3-19f1-4d37-974e-602d8b2ef912.
Title: Feature: Implement global amr_resource registry migration
Menurut user: target sudah independently read back, Backlog, satu root/no children, Feature label, SINGLE-ISSUE-FEATURE-V1 / SINGLE-ISSUE-CHECKLIST-V1 verified. Task ini tidak melakukan Plane read/write/comments, create child, state/label/assignment update. Target Step 0 PENDING, tracking only; tidak menulis paket PRD/UAT target atau mulai implementasi/tests.

2. Explicit scope split / stable ID ledger

Origin | Retained ADDONS13-46 | DEFERRED_TO_FEATURE ADDONS13-57
AC-06 | no-cache addon/library/PyJWKClient/helper, current config/profile/policy/key/credential-ref revision coherence dan synthetic code/config restore simulation | AC-06-M migration code/global inventory/key conversion/conflict reconciliation/versioned global marker/digest/atomicity/idempotence/schema/metadata cleanup/upgrade/apply/full tuple backup-restore rehearsal
UAT-14 | no-cache/config revision simulation; no DB recovery claim | UAT-14-M operational full tuple restore evidence, terkait predecessor UAT-29/G-MIG-04
UAT-24 | clean synthetic current registry model/constraints/ACL/RPC/UI/role/audit/global identity/company authorization proof; declarative company fields/rules/UI absent tetap wajib | UAT-24-M old DB upgrade/columns/metadata/rules/XML/views cleanup
UAT-26 | live helper deny key-as-URL/web.base.url/legacy default, no email auto-binding/resolver preselection/rights expansion | UAT-26-M migration adapter/global legacy inventory/plan/conversion/duplicate-conflict/canonical/idempotence/drift/atomic/concurrency work
UAT-29 | actual current HTTP/auth/session/params/provenance/same-UID/MRO/company-switch/membership-revoke/global config/no-cache/cross-worker revision checks | UAT-29-M legacy-only/candidate-scoped upgrade/dry-run/apply/global marker/idempotence/conflict/schema cleanup/restore rehearsal
R-M01/02/03 | global trust/identity/access/eligibility invariants tetap current dalam risks terkait, bukan current migration completion gate setelah fresh acceptance | same risk IDs OPEN / NOT ACCEPTED, original EV-M01/02/03/EV-APPLY-PLAN, target gates/actions/UNASSIGNED owner-reviewer/candidate PENDING

AC-01..17 dan 25 original case IDs dipertahankan; AC-06 disempitkan secara eksplisit hanya bagian non-migrasi, bukan dihapus. Suffix -M adalah transfer reference, bukan acceptance criteria target yang telah disetujui. Semua current dan transfer case actual NOT RUN atau deferred, tidak ada PASS baru. Normative AC↔UAT edges dibangun ulang dua arah di UAT/RESULT, tidak menyisakan tautan current AC ke migration-only suffix. Historical links di risk records diberi label provenance, bukan active current completion requirements.

D-01–D-11 selain migration delivery split tetap; O-01/O-02 global registry/mapping dan D-06 active current-company enforcement tetap; O-04/O-05 token/introspection/generation contract dan OPN-01/02 CLOSED_BY_EXPLICIT_OWNER_DECISION tetap. No stored Python execution v1, backend ACL/field/RPC safeguards, audience/azp, transport limits, signatures/return shapes/auth precedence/provenance dan evidence/scope rules tidak dilemahkan.

Fresh synthetic/current model validation bukan old DB schema cleanup. Jika current QA memerlukan legacy migration agar bisa diuji, stop sampai target scope/authorization terpisah; bukan izin migrasi atau alasan melepas non-migration criteria. Full rollback tuple requirement tetap tercatat di target; code/config simulation current tidak mengklaim recovery DB.

3. G-MIG-01–04 inherited design approval, scope target only

O-03 tetap APPROVED_FOR_MIGRATION_CODE_IMPLEMENTATION_ONLY — desain/implementasi kode saja, bukan DB/QA/apply/cutover/prod, bukan izin mulai coding/testing target sekarang. Teks berikut diwarisi persis dari PRD Rev.04 §6a untuk menjaga approval provenance; kata Proposal/usulan di dalamnya historis, bukan approval dibuka ulang. Completion seluruh paragraf DEFERRED_TO_FEATURE ADDONS13-57, bukan dikerjakan pada revisi ini:

Proposal G-MIG-01: inventory dan dry-run global satu kali pada QA terotorisasi, termasuk active/archived registry/children, legacy selectors dan resolved values, existing markers/revisions/references serta binding conflicts. Resolve key-indirection persis sekali; missing/invalid references reject tanpa web.base.url atau interpretasi key sebagai URL. Administrator menyetujui plan exact issuer/audience/azp/endpoints/policy/resolver/bindings; jangan meng-union audience atau memilih user/issuer otomatis.

Proposal G-MIG-02: legacy-only membuat satu registry global per exact issuer dari plan disetujui, bukan satu per company; existing candidate rows dipertahankan ID/child/user references bila tidak conflicting. Duplicate issuer/pair yang tidak seharusnya lolos constraint harus terdeteksi termasuk archived; perbedaan endpoint/credential reference/audience/policy/resolver atau satu pair menunjuk user berbeda adalah BLOCKED, bukan first/last-wins, normalize, merge otomatis, atau delete. Identical duplicates pun memerlukan keputusan konsolidasi eksplisit. Active/internal eligibility user diperiksa; membership pada company request tetap runtime, bukan syarat user harus menjadi anggota semua company atau company operator migrasi. Jangan ubah user.company_ids.

Proposal G-MIG-03: migrasi versioned global baru (usulan v2, marker amr_resource.migration.v2.global) dengan digest plan deterministik yang tidak bergantung company aktif; cek marker/revision dan actual rows sebelum no-op. Jangan percaya marker per-company lama sebagai bukti global selesai. Setelah preflight disetujui, transaksi atomic mengonversi data, menghapus definisi field/related company_id dan rule/domain/view terkait pada registry serta merekonsiliasi metadata schema; penanganan kolom lama harus lewat upgrade eksplisit, bukan diasumsikan hilang karena field Python dihapus. Tidak ada penghapusan data sebelum backup dan restore rehearsal. Simpan audit/mapping referensi historis di backup/migration report nonsecret, bukan field registry company_id yang tetap hidup. Failure rollback tanpa partial trust/marker; concurrent apply/create harus dilindungi constraint dan transaksi. Rerun digest sama dari A/B no-op terverifikasi; digest berbeda atau rows drift reject.

Proposal G-MIG-04: backup known-good code+schema+config/reference+audit/cache tuple, dry-run dan QA install/upgrade/idempotence/conflict/restore sebelum cutover; trust edits global harus diaudit dan akses terbatas, tanpa cache v1. Rollback harus memulihkan tuple utuh; downgrade company-scoped tidak boleh memetakan ulang pair/menambah membership diam-diam. Migrasi belum dijalankan atau diuji.

Paragraf tersebut bukan run instruction/authorization target. Current Feature global policy/access/no-cache/identity requirements yang juga disebut di dalamnya tetap current; yang dipindah adalah migration deliverable dan operations evidence. Marker approved string bukan actual marker ditemukan/ditulis. OPN-01/02 tetap closed, M01 inventory UNKNOWN, M02 canonical decisions conditional pending jika conflict ditemukan, M03 target-specific schema/apply/backup-restore PENDING. Semua risiko OPEN / NOT ACCEPTED.

4. Immutable chronology / next gate boundary

Predecessor [Lead disposition](../lead-dispositions/lead-disposition-20261024T134745+0800/LEAD-DISPOSITION.md) SHA-256 29a0cb6b6c36d858e2652f1269fec7b169c285fd0490df7c6695d582c98b0cc9 menerima Rev.04. Itu historical Step 0 acceptance, tidak ditulis ulang.
[Developer report](../developer-step1-20261024T1413+0800/REPORT.md) SHA-256 f98b413168193dcadf5c6a429df54ad418df6cc1656f3f953e62e9e2d6bfabab tetap STEP1_VERDICT=NOT_PASS karena migration/schema belum lengkap, meskipun full offline Python3.7.9 76/76 PASS pada SHA 309c2d883b3475089e70567c3599b7a1858c57e1. User memberikan Lead independent same-suite verification; tidak ada run baru atau raw Lead result dibuat oleh Analis. Green unit bukan migration-safe proof, bukan acceptance.

Lead perlu fresh exact-hash scope review/per-risk disposition, memverifikasi non-migration Step 1 evidence/eligibility pada reported candidate tanpa menulis ulang historical verdict, baru melanjutkan Step 2 unified Code Review secara serial. Step 2 general/manual Security/offline Semgrep satu verdict; Step 3 masih memerlukan accepted review+separate authorized target/runner/runtime/DB/UAT; Step 4 Owner review/PR_ACCEPT dan merge readback, bukan otomatis accepted. Task ini tidak memulai gate-gate tersebut, tidak menjalankan source/product commands, tidak menulis source/tests/Git/Plane.

Fresh acceptance PENDING, acceptance=false. DB/QA/runtime/apply/cutover/prod NOT AUTHORIZED / NOT RUN. Target ADDONS13-57 Step 0, candidate, implementation/testing authorization semua PENDING / NOT GRANTED. Scope transfer bukan residual-risk acceptance atau actual DB change.

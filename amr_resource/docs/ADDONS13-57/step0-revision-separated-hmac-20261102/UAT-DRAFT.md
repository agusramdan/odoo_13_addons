# ADDONS13-57 — UAT superseding DRAFT (separate HMAC addon)

Status: **DRAFT / NOT ACCEPTED**. Semua kasus **NOT RUN**; actual, evidence, runner, candidate, timestamp dan owner: PENDING. Desain test bukan eksekusi atau authorization. Peta AC normative ada di PRD dan setiap kasus di bawah. Fixture harus sintetis, lingkungan terisolasi/target database eksplisit, backup+restore rehearsal dan izin QA/DB terpisah sebelum tindakan. Simpan hasil redacted, SHA kandidat dan artifacts, perintah/selector, versi, assertions, ledger dan evidence path. PASS hanya jika semua expected benar-benar diamati; BLOCKED bila prereq/keputusan belum dipenuhi. Race butuh barrier dan bukti database aktual, fake savepoint bukan bukti transaksi. Setelah run bersihkan hanya resource milik run dan verifikasi tanpa broad prune.

Identitas historis: superseding baseline `98c608f395add60a2e57182726e077167a01d5a5` (Owner-directed rebind; prior `404dcc74b83d682ab3bac8ea20e5e82d9b0849dd` historical only); branch HEAD saat revalidation `da447fa09fac070d4a39c9d2a49bad099de3ec53` (`da447fa`), bukan kandidat implementasi. Revisi berdasarkan keputusan Lead mempertahankan business-company rules dan membership, bukan acceptance atau izin run.

## U01 — Inventory global
- Trace: AC-01; status **NOT RUN**
- Prasyarat: Fixture beberapa company, issuer aktif/archived, children, markers, metadata dan references.
- Langkah: Jalankan inventory/dry-run terotorisasi; bandingkan inventory dengan fixture independen.
- Expected: Semua objek tercatat exact termasuk archived/markers/schema; tidak ada mutation; report nonsecret.
- Actual/evidence: PENDING.

## U02 — Selectors dan plan
- Trace: AC-01, AC-02; status **NOT RUN**
- Prasyarat: Fixture selector valid/invalid dan plan actor.
- Langkah: Dry-run dengan selector valid lalu missing/invalid, URL literal dan web.base.url saja.
- Expected: Key di-resolve sekali; valid mengikuti exact plan; varian invalid reject tanpa fallback; tidak ada write.
- Actual/evidence: PENDING.

## U03 — Plan approval
- Trace: AC-02; status **NOT RUN**
- Prasyarat: Fixture plan lengkap dan digest, issuer I1/I2, azp Z1/Z2, dua revision dan snapshot inventory independen (termasuk archived children/references) yang diikat ke approval.
- Langkah: Setujui plan pertama; secara terpisah ubah issuer, azp, endpoint, audience, credential-ref, policy, resolver dan binding sebelum apply. Pada varian terpisah jangan ubah plan: ubah inventory independen (misalnya tambah archived candidate/child/reference) setelah approval; coba apply untuk setiap varian dan sertakan kontrol tanpa perubahan.
- Expected: Setiap perubahan plan atau inventory independen menolak apply tanpa mutation meski digest plan tetap sama; wajib re-inventory dan approval yang mengikat exact plan/digest serta inventory terbaru. Kontrol tidak berubah memenuhi prereq approval (bukan bukti apply lulus); rahasia tidak muncul di bukti.
- Actual/evidence: PENDING.

## U04 — Legacy-only multi issuer
- Trace: AC-03; status **NOT RUN**
- Prasyarat: Beberapa exact issuer lintas company, active dan archived.
- Langkah: Review plan kemudian apply secara terotorisasi.
- Expected: Satu global row per exact issuer sesuai keputusan; tidak ada union/otomatis pilih user; audit mapping ID.
- Actual/evidence: PENDING.

## U05 — Candidate dan konflik
- Trace: AC-03; status **NOT RUN**
- Prasyarat: Existing candidate kompatibel dengan ID, child, user dan reference historis yang diketahui; duplicate identical dan conflict termasuk archived, perbedaan revision/reference sebagai varian independen.
- Langkah: Dry-run masing-masing; apply hanya kandidat tanpa conflict.
- Expected: ID/child/user references dipertahankan untuk kompatibel dan mapping sebelum/sesudah direkonsiliasi eksplisit terhadap inventory independen; revision/reference mismatch BLOCKED sampai keputusan eksplisit, bukan diasumsikan kompatibel. Semua duplikat/konflik BLOCKED sampai keputusan eksplisit; no auto merge/delete.
- Actual/evidence: PENDING.

## U06 — Eligibility
- Trace: AC-04; status **NOT RUN**
- Prasyarat: Bindings synthetic active internal, inactive, portal, public, superuser dan beda company.
- Langkah: Preflight untuk setiap binding dengan operator company berbeda.
- Expected: Hanya eligible internal diterima; tidak mensyaratkan semua/operator company; company_ids sebelum/sesudah identik.
- Actual/evidence: PENDING.

## U07 — Current company regression
- Trace: AC-04, AC-09; status **NOT RUN**
- Prasyarat: Binding eligible dengan membership company A bukan B, token dan request sintetik.
- Langkah: Autentikasi di A dan B lalu revoke membership A.
- Expected: A diterima sesuai policy, B dan A setelah revoke ditolak; tidak ada privilege/membership expansion.
- Actual/evidence: PENDING.

## U08 — Idempotence lintas company
- Trace: AC-05; status **NOT RUN**
- Prasyarat: Plan disetujui dan hasil apply serta company A/B.
- Langkah: Apply lalu rerun plan sama dari A dan B; periksa marker, digest dan actual graph.
- Expected: Kedua rerun no-op; marker/digest dan graph sama; tidak ada rows baru.
- Actual/evidence: PENDING.

## U09 — Marker dan drift
- Trace: AC-05; status **NOT RUN**
- Prasyarat: Marker lama saja; marker global dengan row hilang, policy/child berubah, revision berbeda, reference hilang/berubah, dan digest berbeda sebagai varian independen; simpan snapshot graph/revision/reference sebagai oracle independen.
- Langkah: Coba preflight/rerun tiap varian.
- Expected: Marker lama tidak membuktikan selesai; digest mismatch, revision drift atau graph/reference drift reject tanpa mutation, termasuk digest plan sama; laporan mengidentifikasi mismatch dan tidak merekonsiliasi otomatis.
- Actual/evidence: PENDING.

## U10 — Atomic rollback
- Trace: AC-06; status **NOT RUN**
- Prasyarat: Synthetic DB dengan backup diverifikasi; injection points disepakati.
- Langkah: Paksa error setelah create, cleanup dan sebelum/sesudah marker di transaksi.
- Expected: Setelah rollback tidak ada partial graph/marker/schema changes; snapshot sebelum/sesudah setara.
- Actual/evidence: PENDING.

## U11 — Concurrent apply/create
- Trace: AC-06; status **NOT RUN**
- Prasyarat: Dua worker disinkronisasi dengan plan sama/berbeda dan concurrent issuer create.
- Langkah: Jalankan race secara deterministik, capture transaksi dan hasil.
- Expected: Satu state konsisten, conflict gagal aman; unique constraints dan locks mencegah duplicate/partial marker.
- Actual/evidence: PENDING.

## U12 — Upgrade cleanup
- Trace: AC-07; status **NOT RUN**
- Prasyarat: Legacy fixture sintetis membedakan field/related, rules/domain/views, metadata, kolom, XML IDs dan references yang terkait registry dari business-company rules non-registry; sertakan beberapa user dengan `res.users.company_ids` berbeda dan references ke objek registry maupun non-registry. Backup dan restore rehearsal lulus sebelum destructive cleanup.
- Langkah: Sebelum upgrade ambil inventory/snapshot independen: identitas, definisi/domain, associations dan hasil akses business-company rules; membership per user; serta source/target references dan mapping registry yang disetujui. Jalankan upgrade eksplisit hanya setelah otorisasi, lalu ambil snapshot independen sesudahnya dan bandingkan tiap item dengan baseline; audit schema, metadata, rules, views, references dan hasil akses fixture yang sama.
- Expected: Hanya field/related `company_id`, rules/domain/views, metadata/kolom legacy terkait registry yang dihapus/direkonsiliasi sesuai plan; business-company rules tetap ada dengan identitas, definisi/domain, associations dan hasil akses sama; setiap `res.users.company_ids` identik sebelum/sesudah, tanpa penambahan atau pengurangan. References non-registry yang harus dipertahankan tetap valid ke target yang sama; registry references sesuai mapping disetujui, tanpa dangling reference. Data/mapping nonsecret tersimpan di backup/report. Perbedaan yang tidak direkonsiliasi atau bukti tidak tersedia berarti BLOCKED/bukan PASS; tidak ada destructive cleanup sebelum rehearsal.
- Actual/evidence: PENDING.

## U13 — Paired backup restore
- Trace: AC-08; status **NOT RUN**
- Prasyarat: Known-good code+DB/schema+filestore+config/reference+audit/cache tuple synthetic, manifest dan hashes.
- Langkah: Ambil backup konsisten, pulihkan lengkap di lingkungan isolasi lalu cek data/refs/attachment bytes relevan.
- Expected: Hashes/provenance cocok, code/schema/config konsisten dan exact attachment/identity/policy dapat dipulihkan; tidak hanya code rollback.
- Actual/evidence: PENDING.

## U14 — Rollback dan downgrade
- Trace: AC-08; status **NOT RUN**
- Prasyarat: Fixture setelah migrasi dan tuple pre-migration yang sudah diverifikasi.
- Langkah: Latih rollback full tuple lalu uji binding/membership dan authorization.
- Expected: Kondisi known-good pulih; tidak ada remap pasangan atau membership diam-diam; hambatan downgrade dilaporkan BLOCKED.
- Actual/evidence: PENDING.

## U15 — Guard dan audit
- Trace: AC-09; status **NOT RUN**
- Prasyarat: Trust admin, code admin, ordinary/portal users serta synthetic secrets.
- Langkah: Coba dry-run/apply per role lalu inspeksi audit dan report.
- Expected: Hanya role terotorisasi; actor, digest dan hasil teraudit tanpa credential/token/secrets; unauthorized tidak write.
- Actual/evidence: PENDING.

## U16 — Install upgrade & regression
- Trace: AC-09; status **NOT RUN**
- Prasyarat: Candidate pinned, clean dan legacy DB isolated, dependencies terverifikasi.
- Langkah: Pada fresh install dan upgrade legacy terisolasi, jalankan native dan offline terarah; secara terpisah uji ACL/RPC per role, global lookup lintas company, HTTP/auth, UI rendered dan no-cache/revision lintas worker dengan perubahan/revoke sintetis. Rekam selector, counts dan observasi tiap assertion; bandingkan native vs unit beserta fixture.
- Expected minimum: unauthorized tidak dapat membaca/menulis trust via ACL/RPC dan role berwenang hanya sesuai hak; issuer exact yang sama menghasilkan identitas global sama lintas company, unknown/inactive ditolak; HTTP token valid + binding/member eligible diterima dan invalid/inactive/nonmember ditolak tanpa privilege expansion; UI rendered memperlihatkan hanya akses sesuai role dan tidak menampilkan field/company rule registry legacy; setelah update policy/key/credential-ref atau revoke, request berikutnya dan worker lain memakai state terbaru tanpa cache stale. Install/upgrade sukses dan assertion terpisah dibuktikan; tiadanya browser/HTTP/cross-worker evidence berarti NOT RUN atau PARTIAL, bukan PASS metadata/unit. Perbedaan native/unit tetap terbuka hingga fixture/oracle diselesaikan; D6 dapat merinci, bukan mengurangi minimum ini.
- Actual/evidence: PENDING.

## Matriks transfer oracle predecessor (provenance, bukan acceptance atau hasil)
Sumber normatif transfer: [DECISION-ADDENDUM-OWNER-SCOPE-DEFER-05](../../ADDONS13-46/analysis-20261024T144710+0800-analis-owner-scope-defer-05/DECISION-ADDENDUM-OWNER-SCOPE-DEFER-05.md) §2 baris 23–37 dan §3 baris 39–51 (path absolut: `/home/ubuntu/docs/reports/ADDONS13-46/analysis-20261024T144710+0800-analis-owner-scope-defer-05/DECISION-ADDENDUM-OWNER-SCOPE-DEFER-05.md`). Setiap baris adalah oracle yang dipindah, bukan klaim semua kasus memenuhi seluruh predecessor. Seluruhnya DRAFT / NOT RUN; perincian yang tidak ditentukan predecessor tetap OPEN menunggu Lead/Owner, tidak dibuat-buat.

| Transfer / sumber | Oracle yang dipindah | AC → kasus spesifik | Reconciliation / batas |
|---|---|---|---|
| AC-06-M; G-MIG-01 | Inventory global active/archived, selectors dan resolved values, marker/revision/reference dan binding conflict; resolve sekali, invalid fail closed; plan exact termasuk issuer/audience/azp | AC-01/02 → U01/U02/U03 | Bandingkan inventory independen; stale approval oleh perubahan plan atau inventory ditolak. |
| AC-06-M; G-MIG-02 | Legacy-only satu global/exact issuer; candidate compatible preserve ID/child/user refs; duplicate termasuk archived dan conflict BLOCKED, identical butuh keputusan; eligibility dan membership | AC-03/04 → U04/U05/U06/U07 | Reconcile mapping/reference sebelum/sesudah; revision/reference drift varian eksplisit U05/U09. Kebijakan resolusi conflict OPEN, tanpa auto merge. |
| AC-06-M; G-MIG-03 | Global versioned marker/digest independen company; cek revision dan actual rows; old marker bukan completion; rerun A/B no-op, digest/rows drift reject | AC-05 → U08/U09 | Fixture revision/reference drift independen, bandingkan graph dan revisions sebelum no-op; canonical field coverage dan semantik revision tepat OPEN D3. |
| AC-06-M; G-MIG-03 | Atomic convert/cleanup dan rollback; concurrent apply/create constraint dan transaksi | AC-06 → U10/U11 | Bukti DB aktual dan barrier setelah otorisasi; exact lock/injection points OPEN D4/D6. |
| AC-06-M; G-MIG-03 | Hapus definisi company field/related rules/domain/views, reconcile schema/metadata/columns eksplisit; historical mapping nonsecret dan backup sebelum penghapusan | AC-07 → U12; AC-08 → U13 | Inventory dan reconcile exact references; U12 secara eksplisit membandingkan preservation business-company rules, membership dan references sebelum/sesudah, sambil membatasi cleanup pada registry. Daftar kolom dan keputusan remediasi unresolved OPEN D4; tidak infer cleanup dari current model. |
| AC-06-M; G-MIG-04 | Full tuple backup/restore, rollback dan downgrade tanpa remap/membership tersembunyi; install/upgrade QA, trust access/audit dan no-cache | AC-08 → U13/U14; AC-09 → U15/U16 | Tuple/restore oracle rinci OPEN D5; U16 minimum current regression tidak menggantikan rehearsal full tuple. |
| UAT-14-M §2 | Operational full tuple restore evidence | AC-08 → U13/U14 | Restore nyata terisolasi, bukan simulasi code/config atau hasil UAT-14 predecessor. |
| UAT-24-M §2 | Old DB upgrade, columns/metadata/rules/XML/views cleanup | AC-07 → U12; AC-09 → U16 | U12 adalah cleanup legacy; U16 clean install/current regression tidak membuktikan old DB cleanup. |
| UAT-26-M §2 | Migration adapter dan global legacy inventory/plan/conversion/duplicate-conflict/canonical/idempotence/drift/atomic/concurrency | AC-01/02 → U01–U03; AC-03/04 → U04–U07; AC-05 → U08/U09; AC-06 → U10/U11 | Tiap varian dinilai terpisah; canonicalisasi dan resolusi konflik OPEN D2/D3, bukan diandaikan. |
| UAT-29-M §2 | Legacy-only/candidate-scoped upgrade, dry-run/apply dan readback, global marker/idempotence/conflict, atomic failure, schema cleanup dan restore rehearsal | AC-01/02 → U01–U03; AC-03 → U04/U05; AC-05 → U08/U09; AC-06 → U10; AC-07 → U12; AC-08 → U13/U14; AC-09 → U16 | U10 memverifikasi rollback atomic failure tanpa partial graph/marker/schema; scenario dan evidence masing-masing; detail predecessor di luar split eksplisit belum jelas, OPEN untuk Lead, tidak mengarang oracle tambahan. |

Transfer hanya oracle migrasi yang disebut rev.05 §2–3; preservation fixture business-company rules/membership adalah batas cleanup upgrade U12, bukan pemindahan seluruh UAT predecessor. Current/non-migration predecessor tetap dipertahankan di ADDONS13-46, bukan dipindah sebagai completion gate di sini; U07/U16 merupakan minimum regresi target yang diusulkan, bukan klaim pemenuhan predecessor. G-MIG approval hanya desain/implementasi dan tidak mengotorisasi eksekusi. Peta AC per kasus di atas dan PRD adalah draft dua arah; semua actual/evidence PENDING.


## Superseding scope and identity (DRAFT / NOT ACCEPTED)
This section supersedes earlier HMAC ownership in `amr_resource`; the Owner directed a separate addon, with `amr_resource_hmac` as a provisional technical name. The source UAT and PRD are unchanged. Accepted source PRD SHA256 `920d946873858c349d08427c93434bf0ce2e877bef4fcfca58b44b2ad2ba2bac`; accepted source UAT SHA256 `7a57d11180f94896dd2361c7d5cbf52f841a574c819bbe6133f1eb58a0c9906f`; accepted D2–D5 proposal SHA256 `48c2f70aea50fa0f84e52b05c892ba2329d970f9dbbe15138b8bd15d9a33757a`. Owner internal comment `26d21ab4` binds baseline `98c608f395add60a2e57182726e077167a01d5a5`. Candidate identity is HEAD plus full combined diff SHA256 `70b9db25139901b69ced3d90cf3d99306355ac972fa99c19b19f4979a99c14f1`; not a test result.

HMAC/key-provider capability belongs to separate `amr_resource_hmac`, proposed for ADDONS13-58. ADDONS13-58 is NOT approved as receiving scope; its own exact PRD/UAT acceptance is required. Ordinary `amr_resource` install/runtime must not depend on it. Dry-run/inventory without addon is allowed only if strictly read-only, with zero mutations and explicit NOT APPLY-ELIGIBLE status. Apply/destructive cleanup stops before mutation without compatible addon/provider and verifiable approval. No unsigned SHA fallback. `_approval_binding.py` is a private offline tracer, not wired into migration and not an HMAC implementation. Canonical-byte ownership, API, approval/audit persistence and version compatibility are unresolved; do not assume an API.

## HMAC integration / fail-closed suite (U17–U25; all NOT RUN)
Each case requires an isolated synthetic fixture, exact candidate/provider compatibility contract, independent before/after state oracle and redacted evidence. Until that interface and receiving task are accepted, cases are BLOCKED for execution and remain NOT RUN.

## U17 — HMAC addon absent
- Trace: AC-02/05/09 + split conditions; status NOT RUN.
- Prerequisite: Fresh isolated install with `amr_resource` only; inventory the migration-relevant tables, markers, schema and references before the test.
- Steps: Run permitted read-only inventory/dry-run. Then attempt apply and destructive cleanup using a synthetic plan and approval placeholder.
- Expected: Base addon installs and ordinary non-apply behavior remains available; dry-run is strictly read-only and reports NOT APPLY-ELIGIBLE; apply/cleanup blocks before any DB/schema/marker/trust-graph mutation. No unsigned digest or first-migration fallback.
- Actual/evidence: PENDING.

## U18 — Provider unavailable or key missing
- Trace: AC-02/05/06 + split conditions; status NOT RUN.
- Prerequisite: Compatible HMAC addon installed in an isolated synthetic target; provider can be independently toggled unavailable, missing current key, and missing historical key.
- Steps: Attempt verification/apply under each provider/key failure variant; capture before/after snapshots.
- Expected: Every variant fails closed before mutation; no fallback to plain SHA, local default, or a newly generated key; user-facing error is generic and does not leak provider details.
- Actual/evidence: PENDING.

## U19 — Provider authorization denied
- Trace: AC-02/09 + split conditions; status NOT RUN.
- Prerequisite: Distinct authorized and unauthorized synthetic service identities; instrument provider calls without recording key material.
- Steps: Attempt approval verification as each identity and attempt arbitrary chosen-message MAC requests through every exposed entrypoint.
- Expected: Only the explicitly authorized caller can request the bounded verification operation; unauthorized and arbitrary-MAC/oracle attempts are rejected before mutation, with no sensitive detail leakage.
- Actual/evidence: PENDING.

## U20 — Binding context mismatch
- Trace: AC-02/05 + split conditions; status NOT RUN.
- Prerequisite: One valid synthetic approval bound to plan, inventory, candidate, schema, purpose and environment.
- Steps: In separate runs alter only purpose, environment, schema version, candidate identity, or compatibility version, leaving other fields unchanged.
- Expected: Every mismatch fails verification before mutation and requires a fresh independently approved record; no normalization or silent rebinding.
- Actual/evidence: PENDING.

## U21 — Wrong tag or key version
- Trace: AC-05/06 + split conditions; status NOT RUN.
- Prerequisite: Valid synthetic tags under two distinct key versions and complete before-state snapshot.
- Steps: Test a corrupted plan tag, corrupted inventory tag, wrong key version, and substituted tag as independent negative variants.
- Expected: Each negative blocks before mutation; comparison uses the approved verifier contract; no re-signing, tag recomputation or fallback that converts invalid evidence to success.
- Actual/evidence: PENDING.

## U22 — Stale independent inventory
- Trace: AC-02/05/06 + split conditions; status NOT RUN.
- Prerequisite: Approved synthetic plan and inventory snapshot; ability to change an inventory-only field/reference after approval while leaving plan bytes unchanged.
- Steps: Add/change an archived issuer or child/reference after approval, independently re-read the inventory, then attempt apply.
- Expected: Verification rejects the stale approval before mutation despite unchanged plan digest; requires fresh inventory and reapproval; graph and marker remain byte/state-equivalent to the pre-attempt snapshot.
- Actual/evidence: PENDING.

## U23 — Key rotation and historical verification
- Trace: AC-05/08 + split conditions; status NOT RUN.
- Prerequisite: Synthetic approval under key version K1, approved rotation to K2, and access-controlled test provider with retained historical version control.
- Steps: Verify a K1 record after rotation using its recorded version; separately remove/deny K1 and try verification; create and verify a new K2 record.
- Expected: Historical K1 record verifies only with K1; missing K1 blocks without replacing it with K2; new K2 record works only for its own approval. No silent re-sign/remap.
- Actual/evidence: PENDING.

## U24 — Secret/error/log leakage
- Trace: AC-09 + split conditions; status NOT RUN.
- Prerequisite: Distinct synthetic markers for key, plan fields, inventory values, tag, credentials and provider errors; capture user errors, application logs, telemetry, ordinary report and restricted audit separately.
- Steps: Trigger success, denial, provider outage, invalid tag and exception paths; scan captured channels for each marker and raw/unkeyed sensitive digest.
- Expected: No key, canonical sensitive bytes, credentials, tags, provider internals or unkeyed sensitive digest appears in ordinary output/log/report/telemetry; restricted audit contains only its explicitly approved protected fields and integrity evidence.
- Actual/evidence: PENDING.

## U25 — Valid compatible-provider positive control
- Trace: AC-02/05/06 + split conditions; status NOT RUN.
- Prerequisite: Compatible addons/provider, approved key version, exact environment/candidate, valid synthetic plan and independently captured unchanged inventory; isolated disposable target and authorized QA run.
- Steps: Verify the valid approval through the real cross-addon integration; in the disposable fixture run only the expected approved migration path, then independently read back graph, marker, schema and audit.
- Expected: The interface accepts only the correctly bound evidence; resulting synthetic state matches the approved plan exactly and is atomic; no raw key/tag/canonical secrets leak. This does not authorize production apply or operation.
- Actual/evidence: PENDING.

**Coverage/count check:** retained suite U01–U16 = 16 cases; added U17–U25 = 9 cases; total 25 unique case IDs. AC-01–09 remain mapped to U01–U16; added split conditions map above. Every case remains NOT RUN; no prior result transfers automatically. U16 must include the dependency-direction/install matrix: `amr_resource` alone installs and ordinary non-apply behavior remains available; HMAC addon requires its base addon; apply without the HMAC capability is blocked before mutation; incompatible provider/addon versions are blocked.

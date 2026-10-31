# ADDONS13-57 — UAT REVISED DRAFT

Semua kasus **NOT RUN**; actual, evidence, runner, candidate, timestamp dan owner: PENDING. Desain test bukan eksekusi atau authorization. Peta AC normative ada di PRD dan setiap kasus di bawah. Fixture harus sintetis, lingkungan terisolasi/target database eksplisit, backup+restore rehearsal dan izin QA/DB terpisah sebelum tindakan. Simpan hasil redacted, SHA kandidat dan artifacts, perintah/selector, versi, assertions, ledger dan evidence path. PASS hanya jika semua expected benar-benar diamati; BLOCKED bila prereq/keputusan belum dipenuhi. Race butuh barrier dan bukti database aktual, fake savepoint bukan bukti transaksi. Setelah run bersihkan hanya resource milik run dan verifikasi tanpa broad prune.

Identitas historis: remote baseline `404dcc74b83d682ab3bac8ea20e5e82d9b0849dd`; branch HEAD saat revalidation `da447fa09fac070d4a39c9d2a49bad099de3ec53` (`da447fa`), bukan kandidat implementasi. Revisi berdasarkan keputusan Lead mempertahankan business-company rules dan membership, bukan acceptance atau izin run.

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

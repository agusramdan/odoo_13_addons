# ADDONS13-64 — UAT v3.1, complete superseding draft

**DRAFT v3.1 — NOT ACCEPTED.** Full superseding review draft; belum mengganti acceptance historis sampai Owner menerima exact hashes. Candidate analisis aktual `4c39fd76cb3818f0fd29cd8c7738fb647e85fde5`, branch `ADDONS13-64`, source committed blobs di `/home/ubuntu/worktrees/ADDONS13-64`. Target produk **Odoo 13 / CPython 3.7.3**, berdasarkan direct Owner. Lead memverifikasi worktree bersih dan diff `6a51c81493b339c67fb97c6615a3e7d758c60251..4c39fd76cb3818f0fd29cd8c7738fb647e85fde5` hanya `AGENTS.md` (commit `agent Python 3.7.3`); source produk identik. Attribution/otorisasi commit tersebut tidak ditebak dan approval dokumen tidak otomatis mengotorisasi push commit itu. Live remote feature masih `6a51c81493b339c67fb97c6615a3e7d758c60251`; target integrasi `origin/main=ac1bcbd66261b92c10078f2a8744a657a3b6490c` cocok live remote. Local main `c08b050cfd85ccc5c705eb92852e57626eb82806` tidak digunakan. Hasil eksperimen tetap historical pada source6a51c81, bukan UATv3.1. Rebinding ini hanya metadata kandidat, tidak mengubah kontrak normatif draftv3. Dokumen analisis/traceability/source-evidence v3 dipertahankan sebagai provenance pra-binding; rujukan terbaru adalah dua dokumen v3.1 dan REBIND-v3.1.json.

## Execution status dan aturan

**Semua kasus v3 NOT RUN.** Analisis ini hanya membaca source/evidence; tidak runtime, install, test, Docker atau UI. Historical 41-test L1/registry/SDK smoke bukan hasil kasus di bawah. PRD-v3.1-DRAFT.md adalah kontrak lengkap; TRACEABILITY.json memuat machine-readable case preconditions/steps/oracles/gates dan mapping dua arah.

Pelaksana QA setelah izin terpisah: source candidate dan any remediation SHA, hashes PRD/UAT/config, approved lock, exact Python3.7.3/Odoo13/images/PG/OS/OpenSSL harus tercatat. Gunakan data sintetis, source ro, no bytecode writes, MemoryTransport hanya di boundary test (record kwargs asli sebelum transport override), network-disabled untuk SDK/L1 dan internal DB-only untuk ORM, tanpa published ports. Semua subcase satu proses fresh bila init/cache berpengaruh. Jangan mengubah safe profile agar tes lulus. Real SDK wajib untuk envelope/integration/global gates; mock/stub boleh unit contract tetapi tidak menggantikan actual capture/persistence. Observer menangkap item types, serialized bytes, init/capture counts, return/re-raise identity, actual DB readback; evidence disanitasi dengan per-channel boolean/location summaries dan hashes tanpa secret nyata.

Status vocabulary: NOT RUN=belum dikerjakan; BLOCKED=prasyarat/decision belum terpenuhi; FAIL=oracle dilanggar meskipun proses exit0; PASS=seluruh subcase oracle dipenuhi pada bound candidate/config. D-EX/D-GLOBAL OPEN tidak boleh disebut PASS. Negative child expected nonzero bukan suite failure dengan sendirinya. Prior browser waiver tidak diwarisi. Tidak ada eksekusi otomatis dari dokumen ini.

## Kasus terstruktur

### UAT-01 — Core-only tanpa optional dependencies

- **Status:** NOT RUN
- **AC:** AC-01, AC-10
- **Prasyarat:** Sandbox core-only bersih; graph prerequisite core lengkap, tanpa sentry_sdk/yaml.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Fresh install amr_service_client; baca registry; lakukan success/error hook dan smoke core.
- **Expected/oracle:** Core installed/usable, SDK tidak terimport/init/capture; prerequisite core yang hilang = BLOCKED, bukan telemetry FAIL.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-02 — Path dan parser

- **Status:** NOT RUN
- **AC:** AC-02
- **Prasyarat:** Fixture file read-only YAML/YML/JSON ekuivalen.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Uji env selector unset/kosong/default; override eksplisit tiap ekstensi; bandingkan parsed mapping.
- **Expected/oracle:** Default /etc/odoo/amr_sentry.yaml; AMR_SENTRY_CONFIG hanya lokasi; namespace SDK dan policy terpisah; format ekuivalen sama.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-03 — Missing/unreadable/malformed/schema

- **Status:** NOT RUN
- **AC:** AC-02, AC-07
- **Prasyarat:** Proses baru per subcase, init spy dan secret marker.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Uji file missing/unreadable, YAML/JSON rusak, null/list root, sentry/policy bukan mapping, ekstensi tak didukung; override invalid dengan default valid.
- **Expected/oracle:** 0 init/capture; warning generik tanpa config/DSN/error text; bisnis usable; override tidak fallback.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-04 — Policy defaults dan tipe

- **Status:** NOT RUN
- **AC:** AC-02, AC-04
- **Prasyarat:** File valid, safe-profile lengkap.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Omit enabled/mode; uji enabled string/int, mode uppercase/unknown, policy unknown key.
- **Expected/oracle:** Omitted => false/none; tipe/enum/key invalid => disabled sebelum init; tidak coercion.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-05 — Profile key hilang — tiap key

- **Status:** NOT RUN
- **AC:** AC-03
- **Prasyarat:** Active valid control dan daftar profile PRD.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Hapus tepat satu dari setiap safety key, dsn tetap valid; proses baru setiap subcase.
- **Expected/oracle:** Semua varian 0 SDK init/events, warning aman; control diterima. Tidak default/repair/inject field hilang.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-06 — Unsafe/wrong type/extra option

- **Status:** NOT RUN
- **AC:** AC-03
- **Prasyarat:** Active valid control.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Setiap bool ubah true/null/string/0; integrations nonempty; max_breadcrumbs 1/false/string; body medium; unknown SDK option; data_collection/with_locals/request_bodies; nonmapping sentry.
- **Expected/oracle:** Setiap nilai tak sesuai exact schema ditolak sebelum init; bool tidak diterima sebagai integer; no retries dengan opsi dikurangi.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-07 — File-only kwargs dan kontaminasi env

- **Status:** NOT RUN
- **AC:** AC-03, AC-09
- **Prasyarat:** Real SDK test-boundary init recorder; file dan env synthetic berbeda.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Aktifkan file aman dengan metadata file eksplisit; seed SENTRY_DSN/ENVIRONMENT/RELEASE/DEBUG; bandingkan input init dan effective options; ulang tanpa dsn file.
- **Expected/oracle:** Privacy kwargs persis file, tanpa hidden defaults adapter; env tak enable/mengganti file; metadata env/host yang tak disetujui => HOLD D-GLOBAL, tidak silently whitelist.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-08 — Matriks mode

- **Status:** NOT RUN
- **AC:** AC-04
- **Prasyarat:** Satu proses per mode, real SDK MemoryTransport.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Sukses/gagal pada all/error/selected/none; selected record persisted opt-in on/off; ulang enabled=false serta dsn absent/empty.
- **Expected/oracle:** Delta all=[1,1], error=[0,1], selected on=[1,1], off=[0,0], none=[0,0]; disabled/DSN kosong 0 init/events; sukses fixed info message.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-09 — Identitas selected dan negative fallback

- **Status:** NOT RUN
- **AC:** AC-04
- **Prasyarat:** Real persisted client A opted-in/B opted-out; effective ORM override.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Call hook eksplisit A di empty self; bound singleton A; explicit B pada bound A; empty/absent client + kw sentry_opt_in=true; non-singleton.
- **Expected/oracle:** A eligible once, explicit B menang dan nol; absent/empty/non-singleton tak dipilih nol; kwargs tidak fallback; tidak restore tags/extra/customer name.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-10 — Outside-hook logging

- **Status:** NOT RUN
- **AC:** AC-05
- **Prasyarat:** Real SDK + safe file; all/error/selected eligible, isolated process.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Log ordinary error sebelum/sesudah hook; simpan effective integration list dan seluruh envelope item types.
- **Expected/oracle:** Outside delta 0; hook delta sesuai mode; integrations []; tidak event/log/trace/metric/session/client-report tambahan.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-11 — Outside-hook unhandled exception

- **Status:** NOT RUN
- **AC:** AC-05
- **Prasyarat:** Child process terkendali, real SDK transport lokal yang bisa diekspor saat exit.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Init safe file, raise synthetic unhandled exception di luar hook; periksa child exit dan captured envelopes.
- **Expected/oracle:** Unhandled business child exit tetap expected nonzero, telemetry delta 0; exit nonzero bukan kegagalan harness; diulang active modes.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-12 — Privacy channel terpisah — bukan exception text

- **Status:** NOT RUN
- **AC:** AC-06
- **Prasyarat:** Real SDK, safe file, safe constant exception text; marker unik per channel.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Seed locals, header, request/response body, credential, kwargs, user/contexts/tags/extra/breadcrumbs/attachments; inspeksi serialized envelopes/transport dan telemetry diagnostics; success/error/selected on/off.
- **Expected/oracle:** Nol marker private, frame vars/source lines dan unwanted attachments; no legacy metadata; off/absent client nol. Lokasi tiap marker dicatat; jangan infer forwarding dari pencarian global.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-13 — Exception-message/path residual terpisah

- **Status:** NOT RUN
- **AC:** AC-06
- **Prasyarat:** Synthetic exception mengandung marker hanya pada text/path, bukan locals/private args.
- **Gate:** D-EX OPEN: Owner memilih kontrak exception; probe hanya setelah izin sandbox
- **Langkah:** Capture original exception dan chained exception melalui hook; cari marker text/path dalam serialized bytes; catat lokasi dan putusan Owner D-EX.
- **Expected/oracle:** Tidak klaim zero arbitrary data. Bila marker lolos, strict privacy FAIL/HOLD; hanya keputusan eksplisit scoped residual atau revisi kontrak telemetry dapat menutup gate. Tidak custom scrubber/replace exception otomatis.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-14 — SDK global/current/isolation dan integrasi lain

- **Status:** NOT RUN
- **AC:** AC-06, AC-09
- **Prasyarat:** Real SDK2, proses terpisah; marker scope dan another-client fixture.
- **Gate:** D-GLOBAL OPEN: exclusivity constraint/design review + otorisasi sandbox
- **Langkah:** Seed global/current/isolation metadata/processors; simulasi SDK lain initialized sebelum/sesudah bootstrap; capture hook; bandingkan routing/client/DSN dan scope.
- **Expected/oracle:** Tidak bocor metadata atau salah client/DSN. Kontaminasi = FAIL/HOLD; fresh/new/isolation_scope bukan bukti cukup; proses non-eksklusif tidak diterima tanpa desain baru.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-15 — call return/exception dan SDK failures

- **Status:** NOT RUN
- **AC:** AC-07
- **Prasyarat:** Actual ServiceClient.call, synthetic request transport; baseline business oracle direkam.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Uji success response identity, HTTP error dan prepare/request error; injeksi import/init failure, capture_message failure, capture_exception failure, transport failure secara terpisah.
- **Expected/oracle:** Return/re-raise identity dan raise_exception behavior sama baseline; SDK failure tidak escape; diagnostics aman; pre-assignment response defect dicatat terpisah, bukan silently fixed.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-16 — Persisted dispatch/log

- **Status:** NOT RUN
- **AC:** AC-07, AC-08
- **Prasyarat:** Actual registry; create+commit synthetic service client/endpoint/credential dan log records.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Jalankan ServiceClientSend.dispatch_send success/error active_log on/off; log.send dan log.dispatch_send; baca state/response/client/log count via fresh cursor.
- **Expected/oracle:** Business return/state/exception/log persistence sesuai source/baseline; hook tepat per outcome; capture/transport failure tak mengubah business persistence. model.new() saja tidak cukup.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-17 — Actions dan deduplikasi

- **Status:** NOT RUN
- **AC:** AC-07, AC-08
- **Prasyarat:** Persisted action fixtures dengan handler/error handler/next action.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Jalankan request-failure, request-success+handler-failure, next-action-failure; ulang SDK failures.
- **Expected/oracle:** Request failure tak ditangkap ulang action; request-success+handler-failure boleh dua outcome; handler/return/business error sama baseline; no auto logging event tambahan.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-18 — Bootstrap/restart/multi-registry

- **Status:** NOT RUN
- **AC:** AC-09
- **Prasyarat:** Dua DB disposable, worker/preload topology dicatat.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Import ulang dalam proses sama; edit salinan config lalu sebelum/sesudah restart; install optional hanya DB A, buka DB B; ulang worker/fork topology.
- **Expected/oracle:** Sekali init per proses sesuai kontrak; config baru hanya setelah restart; tidak reporting DB B/tenant lain tanpa authority. Jika process-wide SDK tak bisa memenuhi => HOLD D-GLOBAL, bukan ubah jadi init per DB.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-19 — Exact interpreter/dependency full graph

- **Status:** NOT RUN
- **AC:** AC-10
- **Prasyarat:** Approved disposable digest/lock dan artifact provenance, bukan live environment.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Rekam Python patch, Odoo/OS/OpenSSL/PG, full pip freeze/list/check baseline+candidate dan import paths; review full constraints Odoo versus sandbox override.
- **Expected/oracle:** Python tepat 3.7.3/Odoo13; pip check 0 dan graph/provenance lengkap; Requests adjustment test-only eksplisit; tidak no-deps/ignore-installed; bukan security approval.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-20 — Optional fresh install dan upgrade

- **Status:** NOT RUN
- **AC:** AC-01, AC-10
- **Prasyarat:** Fresh DB plus separate upgrade fixture/checkpoint; real SDK/PyYAML declared prerequisites.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Fresh install amr_service_client,amr_sentry; upgrade seeded baseline fixture; readback module states/registry/models/opt-in; ulang safe policy smoke.
- **Expected/oracle:** Fresh dan upgrade keduanya installed/usable; effective optional override dibuktikan capture, bukan hanya callable; missing declared dependency = BLOCKED prerequisite, bukan janji fallback import yaml.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-21 — Settings/UI/docs operator

- **Status:** NOT RUN
- **AC:** AC-09, AC-11
- **Prasyarat:** Registry/UI sandbox; draft README/operator perubahan sesuai PRD.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Review root/addon README links dan complete examples; inspect global Settings removed; toggle per-client opt-in; seed old ir.config_parameter; render UI.
- **Expected/oracle:** Old settings tidak efektif; opt-in ada dan berpengaruh selected; docs target3.7.3 dan test-only dependency caveat benar; browser waiver lama tak diwarisi; examples valid JSON/YAML.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-22 — Containment/no-egress

- **Status:** NOT RUN
- **AC:** AC-05, AC-12
- **Prasyarat:** DB/network namespace internal-only tanpa published ports; MemoryTransport test-only override.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Sebelum init aktifkan network isolation, DNS/socket/HTTP monitoring/guards (DB:5432 only); jalankan suite, inspect denied and successful calls plus all envelope types.
- **Expected/oracle:** 0 non-DB DNS/network attempt/success dari tested paths; zero-egress dibuktikan berlapis, bukan .invalid DSN; hook envelope tetap local. Test transport injection satu-satunya approved kwargs test exception dan dicatat.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-23 — Evidence/approval binding

- **Status:** NOT RUN
- **AC:** AC-12
- **Prasyarat:** Accepted exact-hash docs dan authorized remediation SHA baru bila ada.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Validasi sha candidate/base/source blobs, config hash, images/lock/oracles; catat status seluruh subcase, command argv/exit dan sanitized evidence manifest.
- **Expected/oracle:** Historical logs hanya provenance; tak ada UAT PASS diturunkan dari exit0/L1; changed SHA/config wajib rebind; seluruh subcase dihitung dan setiap AC punya oracle.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

### UAT-24 — Rollback rehearsal dan cleanup exact IDs

- **Status:** NOT RUN
- **AC:** AC-10, AC-12
- **Prasyarat:** Run-owned resource inventory sebelum create; baseline immutable.
- **Gate:** Owner exact-hash approval + otorisasi terpisah runtime sandbox
- **Langkah:** Rehearse disabled/none+restart dan restore fixture; drop/readback exact DBs sebelum PG hilang; remove run-owned containers/networks/images/volumes dan inspect tiap ID termasuk anonymous Odoo volumes.
- **Expected/oracle:** Core tetap usable, optional disabled; exact DB absence dan per-ID volume absence tercatat; baseline preserved; tidak broad prune. Resource tanpa ID = cleanup gap/HOLD, bukan full cleanup PASS.
- **Evidence wajib:** argv/exit dan config/source/env hashes; init/capture/envelope deltas atau registry/UI/DB readback sesuai oracle; setiap subcase dicatat terpisah, tanpa aggregate green yang menyembunyikan FAIL.

## Keputusan verdict dan sign-off

1. QA melampirkan tabel semua kasus dan subcase, unexpected payload channel/type, seluruh resource IDs dan absence readbacks. AC coverage bukan kelulusan tes. Evidence cleanup lama tanpa Odoo volume IDs tidak memenuhi UAT24 baru.
2. UAT13 exception text dan UAT14/18 SDK global adalah gate terpisah: zero-locals tidak menutup exception text; integrations=[] tidak menutup ambient scope/global SDK contamination. Tidak melemahkan oracle setelah hasil keluar tanpa revisi/Owner approval baru.
3. Lead rebind candidate jika source berubah; Owner memilih D-EX/D-GLOBAL, menerima exact-hash spec baru; QA menentukan actual PASS/FAIL, bukan mengganti status lewat approval. Tidak issue closure/PR_ACCEPT/deploy otomatis. Full-stack advisory/security dan production approval tetap terpisah.

## AC coverage

- AC-01: UAT-01, UAT-20
- AC-02: UAT-02, UAT-03, UAT-04
- AC-03: UAT-05, UAT-06, UAT-07
- AC-04: UAT-04, UAT-08, UAT-09
- AC-05: UAT-10, UAT-11, UAT-22
- AC-06: UAT-12, UAT-13, UAT-14
- AC-07: UAT-03, UAT-15, UAT-16, UAT-17
- AC-08: UAT-16, UAT-17
- AC-09: UAT-07, UAT-14, UAT-18, UAT-21
- AC-10: UAT-01, UAT-19, UAT-20, UAT-24
- AC-11: UAT-21
- AC-12: UAT-22, UAT-23, UAT-24

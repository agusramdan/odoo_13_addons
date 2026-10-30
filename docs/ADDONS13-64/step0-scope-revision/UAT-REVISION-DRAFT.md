# ADDONS13-64 — UAT revisi scope: DRAFT, NOT ACCEPTED

Baseline `cc901a2ae8695c61827850bc5191983fc94dc02d`; versi asal accepted `docs/ADDONS13-64/step0-v3.1-20261030/UAT-v3.1-DRAFT.md` hash `508da8bd2bc6ed6d1f6f98568a2e61418d204750152a8a21f59b3620579eb81e`. Matriks ini mengusulkan penugasan bukan membatalkan oracle asal. S=64, F=68, P=prasyarat keselamatan; setiap kasus baru **NOT RUN**, bukan klaim bahwa evidence historis belum pernah ada. Hasil historis lihat PRD dan laporan masing-masing. Tidak menghilangkan subcase accepted; bila uji lintas issue diperlukan, 64 tetap HOLD hingga evidence candidate-bound dan acceptance berlaku.

Prasyarat umum: Owner menerima exact-hash PRD/UAT revisi, izin runtime sandbox terpisah, candidate SHA/config/image/lock tercatat; Odoo13/Python3.7.3, data sintetis, no-egress, sumber read-only, DB/network disposable. Baca outcome dan cleanup per-resource bukan exit wrapper saja. Semua langkah dan oracle di bawah diambil dari TRACEABILITY v3 accepted; detail dan subcase lengkap mengacu UAT accepted, termasuk profile 12 key dan aturan type, tanpa mengubah oracle setelah hasil keluar.

| UAT | Judul / AC | Penempatan | Status baru |
|---|---|---|---|
| UAT-01 | Core-only tanpa optional dependencies / AC-01, AC-10 | S+P | NOT RUN |
| UAT-02 | Path dan parser / AC-02 | S+P | NOT RUN |
| UAT-03 | Missing/unreadable/malformed/schema / AC-02, AC-07 | S+P | NOT RUN |
| UAT-04 | Policy defaults dan tipe / AC-02, AC-04 | S+P | NOT RUN |
| UAT-05 | Profile key hilang — tiap key / AC-03 | S+P | NOT RUN |
| UAT-06 | Unsafe/wrong type/extra option / AC-03 | S+P | NOT RUN |
| UAT-07 | File-only kwargs dan kontaminasi env / AC-03, AC-09 | F+P provenance | NOT RUN |
| UAT-08 | Matriks mode / AC-04 | S+P | NOT RUN |
| UAT-09 | Identitas selected dan negative fallback / AC-04 | S+P | NOT RUN |
| UAT-10 | Outside-hook logging / AC-05 | S+P | NOT RUN |
| UAT-11 | Outside-hook unhandled exception / AC-05 | S+P | NOT RUN |
| UAT-12 | Privacy channel terpisah — bukan exception text / AC-06 | F+P ambient privacy | NOT RUN |
| UAT-13 | Exception-message/path residual terpisah / AC-06 | F+P strict oracle & D-EX | NOT RUN |
| UAT-14 | SDK global/current/isolation dan integrasi lain / AC-06, AC-09 | F+P global scope/exclusivity | NOT RUN |
| UAT-15 | call return/exception dan SDK failures / AC-07 | S+P | NOT RUN |
| UAT-16 | Persisted dispatch/log / AC-07, AC-08 | F+P dispatch core-only dan dedup | NOT RUN |
| UAT-17 | Actions dan deduplikasi / AC-07, AC-08 | S+P | NOT RUN |
| UAT-18 | Bootstrap/restart/multi-registry / AC-09 | S+F+P process/tenant | NOT RUN |
| UAT-19 | Exact interpreter/dependency full graph / AC-10 | S+P | NOT RUN |
| UAT-20 | Optional fresh install dan upgrade / AC-01, AC-10 | S+P upgrade dependency | NOT RUN |
| UAT-21 | Settings/UI/docs operator / AC-09, AC-11 | S+F+P historical FAIL; HEAD verdict pending | NOT RUN |
| UAT-22 | Containment/no-egress / AC-05, AC-12 | S+P | NOT RUN |
| UAT-23 | Evidence/approval binding / AC-12 | S+P | NOT RUN |
| UAT-24 | Rollback rehearsal dan cleanup exact IDs / AC-10, AC-12 | S+P | NOT RUN |

## Langkah dan oracle per kasus

### UAT-01 — Core-only tanpa optional dependencies
**Status:** NOT RUN. **Prasyarat:** Sandbox core-only bersih; graph prerequisite core lengkap, tanpa sentry_sdk/yaml.

**Langkah:** Fresh install amr_service_client; baca registry; lakukan success/error hook dan smoke core.

**Oracle:** Core installed/usable, SDK tidak terimport/init/capture; prerequisite core yang hilang = BLOCKED, bukan telemetry FAIL.

### UAT-02 — Path dan parser
**Status:** NOT RUN. **Prasyarat:** Fixture file read-only YAML/YML/JSON ekuivalen.

**Langkah:** Uji env selector unset/kosong/default; override eksplisit tiap ekstensi; bandingkan parsed mapping.

**Oracle:** Default /etc/odoo/amr_sentry.yaml; AMR_SENTRY_CONFIG hanya lokasi; namespace SDK dan policy terpisah; format ekuivalen sama.

### UAT-03 — Missing/unreadable/malformed/schema
**Status:** NOT RUN. **Prasyarat:** Proses baru per subcase, init spy dan secret marker.

**Langkah:** Uji file missing/unreadable, YAML/JSON rusak, null/list root, sentry/policy bukan mapping, ekstensi tak didukung; override invalid dengan default valid.

**Oracle:** 0 init/capture; warning generik tanpa config/DSN/error text; bisnis usable; override tidak fallback.

### UAT-04 — Policy defaults dan tipe
**Status:** NOT RUN. **Prasyarat:** File valid, safe-profile lengkap.

**Langkah:** Omit enabled/mode; uji enabled string/int, mode uppercase/unknown, policy unknown key.

**Oracle:** Omitted => false/none; tipe/enum/key invalid => disabled sebelum init; tidak coercion.

### UAT-05 — Profile key hilang — tiap key
**Status:** NOT RUN. **Prasyarat:** Active valid control dan daftar profile PRD.

**Langkah:** Hapus tepat satu dari setiap safety key, dsn tetap valid; proses baru setiap subcase.

**Oracle:** Semua varian 0 SDK init/events, warning aman; control diterima. Tidak default/repair/inject field hilang.

### UAT-06 — Unsafe/wrong type/extra option
**Status:** NOT RUN. **Prasyarat:** Active valid control.

**Langkah:** Setiap bool ubah true/null/string/0; integrations nonempty; max_breadcrumbs 1/false/string; body medium; unknown SDK option; data_collection/with_locals/request_bodies; nonmapping sentry.

**Oracle:** Setiap nilai tak sesuai exact schema ditolak sebelum init; bool tidak diterima sebagai integer; no retries dengan opsi dikurangi.

### UAT-07 — File-only kwargs dan kontaminasi env
**Status:** NOT RUN. **Prasyarat:** Real SDK test-boundary init recorder; file dan env synthetic berbeda.

**Langkah:** Aktifkan file aman dengan metadata file eksplisit; seed SENTRY_DSN/ENVIRONMENT/RELEASE/DEBUG; bandingkan input init dan effective options; ulang tanpa dsn file.

**Oracle:** Privacy kwargs persis file, tanpa hidden defaults adapter; env tak enable/mengganti file; metadata env/host yang tak disetujui => HOLD D-GLOBAL, tidak silently whitelist.

### UAT-08 — Matriks mode
**Status:** NOT RUN. **Prasyarat:** Satu proses per mode, real SDK MemoryTransport.

**Langkah:** Sukses/gagal pada all/error/selected/none; selected record persisted opt-in on/off; ulang enabled=false serta dsn absent/empty.

**Oracle:** Delta all=[1,1], error=[0,1], selected on=[1,1], off=[0,0], none=[0,0]; disabled/DSN kosong 0 init/events; sukses fixed info message.

### UAT-09 — Identitas selected dan negative fallback
**Status:** NOT RUN. **Prasyarat:** Real persisted client A opted-in/B opted-out; effective ORM override.

**Langkah:** Call hook eksplisit A di empty self; bound singleton A; explicit B pada bound A; empty/absent client + kw sentry_opt_in=true; non-singleton.

**Oracle:** A eligible once, explicit B menang dan nol; absent/empty/non-singleton tak dipilih nol; kwargs tidak fallback; tidak restore tags/extra/customer name.

### UAT-10 — Outside-hook logging
**Status:** NOT RUN. **Prasyarat:** Real SDK + safe file; all/error/selected eligible, isolated process.

**Langkah:** Log ordinary error sebelum/sesudah hook; simpan effective integration list dan seluruh envelope item types.

**Oracle:** Outside delta 0; hook delta sesuai mode; integrations []; tidak event/log/trace/metric/session/client-report tambahan.

### UAT-11 — Outside-hook unhandled exception
**Status:** NOT RUN. **Prasyarat:** Child process terkendali, real SDK transport lokal yang bisa diekspor saat exit.

**Langkah:** Init safe file, raise synthetic unhandled exception di luar hook; periksa child exit dan captured envelopes.

**Oracle:** Unhandled business child exit tetap expected nonzero, telemetry delta 0; exit nonzero bukan kegagalan harness; diulang active modes.

### UAT-12 — Privacy channel terpisah — bukan exception text
**Status:** NOT RUN. **Prasyarat:** Real SDK, safe file, safe constant exception text; marker unik per channel.

**Langkah:** Seed locals, header, request/response body, credential, kwargs, user/contexts/tags/extra/breadcrumbs/attachments; inspeksi serialized envelopes/transport dan telemetry diagnostics; success/error/selected on/off.

**Oracle:** Nol marker private, frame vars/source lines dan unwanted attachments; no legacy metadata; off/absent client nol. Lokasi tiap marker dicatat; jangan infer forwarding dari pencarian global.

### UAT-13 — Exception-message/path residual terpisah
**Status:** NOT RUN. **Prasyarat:** Synthetic exception mengandung marker hanya pada text/path, bukan locals/private args.

**Langkah:** Capture original exception dan chained exception melalui hook; cari marker text/path dalam serialized bytes; catat lokasi dan putusan Owner D-EX.

**Oracle:** Tidak klaim zero arbitrary data. Bila marker lolos, strict privacy FAIL/HOLD; hanya keputusan eksplisit scoped residual atau revisi kontrak telemetry dapat menutup gate. Tidak custom scrubber/replace exception otomatis.

### UAT-14 — SDK global/current/isolation dan integrasi lain
**Status:** NOT RUN. **Prasyarat:** Real SDK2, proses terpisah; marker scope dan another-client fixture.

**Langkah:** Seed global/current/isolation metadata/processors; simulasi SDK lain initialized sebelum/sesudah bootstrap; capture hook; bandingkan routing/client/DSN dan scope.

**Oracle:** Tidak bocor metadata atau salah client/DSN. Kontaminasi = FAIL/HOLD; fresh/new/isolation_scope bukan bukti cukup; proses non-eksklusif tidak diterima tanpa desain baru.

### UAT-15 — call return/exception dan SDK failures
**Status:** NOT RUN. **Prasyarat:** Actual ServiceClient.call, synthetic request transport; baseline business oracle direkam.

**Langkah:** Uji success response identity, HTTP error dan prepare/request error; injeksi import/init failure, capture_message failure, capture_exception failure, transport failure secara terpisah.

**Oracle:** Return/re-raise identity dan raise_exception behavior sama baseline; SDK failure tidak escape; diagnostics aman; pre-assignment response defect dicatat terpisah, bukan silently fixed.

### UAT-16 — Persisted dispatch/log
**Status:** NOT RUN. **Prasyarat:** Actual registry; create+commit synthetic service client/endpoint/credential dan log records.

**Langkah:** Jalankan ServiceClientSend.dispatch_send success/error active_log on/off; log.send dan log.dispatch_send; baca state/response/client/log count via fresh cursor.

**Oracle:** Business return/state/exception/log persistence sesuai source/baseline; hook tepat per outcome; capture/transport failure tak mengubah business persistence. model.new() saja tidak cukup.

### UAT-17 — Actions dan deduplikasi
**Status:** NOT RUN. **Prasyarat:** Persisted action fixtures dengan handler/error handler/next action.

**Langkah:** Jalankan request-failure, request-success+handler-failure, next-action-failure; ulang SDK failures.

**Oracle:** Request failure tak ditangkap ulang action; request-success+handler-failure boleh dua outcome; handler/return/business error sama baseline; no auto logging event tambahan.

### UAT-18 — Bootstrap/restart/multi-registry
**Status:** NOT RUN. **Prasyarat:** Dua DB disposable, worker/preload topology dicatat.

**Langkah:** Import ulang dalam proses sama; edit salinan config lalu sebelum/sesudah restart; install optional hanya DB A, buka DB B; ulang worker/fork topology.

**Oracle:** Sekali init per proses sesuai kontrak; config baru hanya setelah restart; tidak reporting DB B/tenant lain tanpa authority. Jika process-wide SDK tak bisa memenuhi => HOLD D-GLOBAL, bukan ubah jadi init per DB.

### UAT-19 — Exact interpreter/dependency full graph
**Status:** NOT RUN. **Prasyarat:** Approved disposable digest/lock dan artifact provenance, bukan live environment.

**Langkah:** Rekam Python patch, Odoo/OS/OpenSSL/PG, full pip freeze/list/check baseline+candidate dan import paths; review full constraints Odoo versus sandbox override.

**Oracle:** Python tepat 3.7.3/Odoo13; pip check 0 dan graph/provenance lengkap; Requests adjustment test-only eksplisit; tidak no-deps/ignore-installed; bukan security approval.

### UAT-20 — Optional fresh install dan upgrade
**Status:** NOT RUN. **Prasyarat:** Fresh DB plus separate upgrade fixture/checkpoint; real SDK/PyYAML declared prerequisites.

**Langkah:** Fresh install amr_service_client,amr_sentry; upgrade seeded baseline fixture; readback module states/registry/models/opt-in; ulang safe policy smoke.

**Oracle:** Fresh dan upgrade keduanya installed/usable; effective optional override dibuktikan capture, bukan hanya callable; missing declared dependency = BLOCKED prerequisite, bukan janji fallback import yaml.

### UAT-21 — Settings/UI/docs operator
**Status:** NOT RUN. **Prasyarat:** Registry/UI sandbox; draft README/operator perubahan sesuai PRD.

**Langkah:** Review root/addon README links dan complete examples; inspect global Settings removed; toggle per-client opt-in; seed old ir.config_parameter; render UI.

**Oracle:** Old settings tidak efektif; opt-in ada dan berpengaruh selected; docs target3.7.3 dan test-only dependency caveat benar; browser waiver lama tak diwarisi; examples valid JSON/YAML.

### UAT-22 — Containment/no-egress
**Status:** NOT RUN. **Prasyarat:** DB/network namespace internal-only tanpa published ports; MemoryTransport test-only override.

**Langkah:** Sebelum init aktifkan network isolation, DNS/socket/HTTP monitoring/guards (DB:5432 only); jalankan suite, inspect denied and successful calls plus all envelope types.

**Oracle:** 0 non-DB DNS/network attempt/success dari tested paths; zero-egress dibuktikan berlapis, bukan .invalid DSN; hook envelope tetap local. Test transport injection satu-satunya approved kwargs test exception dan dicatat.

### UAT-23 — Evidence/approval binding
**Status:** NOT RUN. **Prasyarat:** Accepted exact-hash docs dan authorized remediation SHA baru bila ada.

**Langkah:** Validasi sha candidate/base/source blobs, config hash, images/lock/oracles; catat status seluruh subcase, command argv/exit dan sanitized evidence manifest.

**Oracle:** Historical logs hanya provenance; tak ada UAT PASS diturunkan dari exit0/L1; changed SHA/config wajib rebind; seluruh subcase dihitung dan setiap AC punya oracle.

### UAT-24 — Rollback rehearsal dan cleanup exact IDs
**Status:** NOT RUN. **Prasyarat:** Run-owned resource inventory sebelum create; baseline immutable.

**Langkah:** Rehearse disabled/none+restart dan restore fixture; drop/readback exact DBs sebelum PG hilang; remove run-owned containers/networks/images/volumes dan inspect tiap ID termasuk anonymous Odoo volumes.

**Oracle:** Core tetap usable, optional disabled; exact DB absence dan per-ID volume absence tercatat; baseline preserved; tidak broad prune. Resource tanpa ID = cleanup gap/HOLD, bukan full cleanup PASS.

## Gate keselamatan lintas issue dan evidence

- UAT-16: tambah pembandingan baseline vs kandidat pada core-only serta optional disabled/enabled, success/error, active_log on/off, log.send/log.dispatch_send, injeksi kegagalan capture/transport, identity outcome dan fresh-cursor persistence; dokumentasikan event kind dan jumlah, termasuk preparasi/request failure. Eksperimen historis tidak mencakup seluruh ini. Tidak mendeskripsikan defect sebagai regresi sebelum baseline dibandingkan.
- UAT-07/12/13/14/18: catat provenance file/env/host di effective SDK/envelope, ambient user/context/tags/extras/attachments, semua item dan penanda sintetis; bedakan pengujian yang melanggar eksklusivitas dari pengujian compliant. Keputusan D-EX yang sudah diterima tidak mengubah strict hasil historis dan bukan blanket privacy approval. D-GLOBAL sudah memilih exclusivity, buktikan di topology/worker/DB; bukan membuka ulang pilihan.
- UAT-19/20: full dependency inventory, isolated lock & pip check, exact interpreter, production compatibility/security adalah gate lain; UAT-20 PARTIAL tidak otomatis PASS. UAT-21 pada HEAD log fresh belum ada verdict final agregat; historical FAIL tetap.
- UAT-22–24: bukti egress monitoring, per-case argv/exit, exact candidate + config + spec + environment, ID containers/network/volumes/DB dan readback absence; rehearsal disable/restart dan rollback pada sandbox bukan perintah ke production. Setiap subcase berstatus independen. Tiada tes pada penyusunan dokumen ini.

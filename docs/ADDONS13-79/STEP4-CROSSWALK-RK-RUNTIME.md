# ADDONS13-79 Step 4 — crosswalk R/K/runtime dan rancangan harness

> **Batas waktu:** bagian historis sampai `Hitungan dan blockers` adalah desain statis pada `f26a674270467c85b7750073e085e9955e5461e1`; actual UAT **NOT RUN pada saat itu**. Rekonsiliasi Gen5 sesudahnya dicatat terpisah di akhir; tidak mengganti atau mengubah historical actual tersebut.

**STATIC DESIGN ONLY — seluruh actual UAT NOT RUN.** Tidak ada database, container, build/pull, integration test, UAT, atau suite dijalankan. Dokumen ini bukan konfigurasi final, rebind, waiver, approval scope, bukti propagasi, ataupun implementasi harness. `UAT.md` SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; `ACCEPTANCE-METADATA.md` mengikat persetujuan Owner pada byte tersebut meskipun label internalnya draft. Metadata itu tidak memberi rebind/izin runtime. Sumber diperiksa pada branch `ADDONS13-79`, HEAD `f26a674270467c85b7750073e085e9955e5461e1`; rebind sebelumnya hanya `0ebf9ac745450b9b3f0555829490b3c3b0978f79`. Delta keduanya terdiri dari enam file dokumentasi; tetap diperlukan rebind eksplisit kandidat yang akan diuji, termasuk inventaris dirty/snapshot. `STEP4-ATOMIC-D01-AND-HARNESS-DRAFT.md` tetap menjadi rincian D01; dokumen ini tidak mengklaim melengkapi semua keluarga lain. SCOPE-01 OPEN; keputusan fresh mapping/profile, route-helper, lifecycle, acceptance risiko dan waiver terpisah tetap belum diputuskan oleh persetujuan spesifikasi.

## Cara membaca crosswalk

Setiap baris adalah observable atomik untuk sepuluh ID yang diminta; beberapa ID sengaja berbagi observable, bukan deduplikasi kasus. **GAP** = belum ada assert/rekaman memadai yang ditemukan pada sumber terbatas ini; bukan klaim tidak ada di seluruh dunia. **PARTIAL** = assert spesifik ada dalam source, namun tidak memenuhi seluruh observable atau batasnya. Tidak satu pun label berarti test dikoleksi atau lulus. Actor dan fixture berikut bersifat synthetic nonproduksi; security owner, deployment owner, incident owner, trust admin dan Tester masing-masing adalah peran berbeda, bukan fiktif yang dianggap sudah ditunjuk. Untuk rotation gunakan K dan R RSA sintetis berbeda, token K lama dan token K baru yang dipalsukan setelah kompromi, keduanya belum expired; trust JWKS dan local PEM dikonfigurasi independen; inventaris verifier/worker/region yang sebenarnya harus disetujui dan dibuktikan, bukan satu fixture DB dianggap global. Isolasi jaringan bukan observer percobaan jaringan.

Referensi source pendek, dengan kelas dan discovery:

- **S1** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_jwks_rsa_selection_and_no_cache` L369–380: dua validasi, `fetch.call_count == 2`, lalu masing-masing JWKS kosong/duplikat atau metadata tidak benar ditolak. Fixture fake fetch/profile dan token sintetis; offline unit, **bukan** native. Tidak memeriksa insiden, PEM, propagasi atau forged token.
- **S2** `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_signing_configuration_change_uses_new_key_and_ttl` L112–127: konfigurasi HS256 sintetis berubah, exp token baru tepat dan token lama gagal diverifikasi dengan secret baru. Top-level `amr_oidc_resource/tests/__init__.py` mengekspos modul langsung; native discovery NOT RUN. Ini pergantian signing secret lokal, bukan penghapusan trust verifier terdistribusi.
- **S3** `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197–223: assert manifest glue dependencies, `auto_install=False`, deklarasi lima metode pada glue/RS dan tidak pada provider. Offline unit AST/manifest, tidak membuktikan registry/MRO atau semua extension.
- **S4** `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_url_helpers_reject_bearer_creation` L225–248: synthetic URL, kedua helper raise `UserError`, mock `get_access_token` tidak dipanggil; offline unit, bukan RPC, route, signer/cache atau runtime MRO.
- **S5** `amr_resource/tests/integration/test_contracts.py::TestResourceContracts::test_ut08_user_predicates_environment_and_stubs` L170: direct issuance ditolak dan URL passthrough di fixture ORM. `amr_resource/tests/__init__.py` hanya mengekspos package `integration`, bukan nama test module; native loader/discovery NOT RUN.
- **S6** `amr_oidc/tests/unit/test_standalone_package.py::StandalonePackageTests::test_provider_manifest_does_not_require_token_or_resource_addons` L39: pengecualian manifest provider; offline, tidak membuktikan manifest RS, install atau closure.
- **S7** `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_pinned_dependency_and_python_runtime` L99–109 mengharapkan Python **3.8.20**, bukan target 3.7.3; assertion historis bukan pengukuran runtime atau kompatibilitas.

Offline unit tidak terdaftar sebagai native integration; `amr_oidc/tests/__init__.py` mengekspos langsung sepuluh modul termasuk `test_public_key_orm` dan `test_provider_selected_uat`, tetapi tidak `test_helper_decode` maupun `test_access_token_audience_presence`. Loader Odoo yang tepat belum source-verified, jadi paparan statis bukan bukti discovery. Jangan mem-bypass guard layout provider (`test_resource_glue_contract.py` L103–122), mengimpor test di production addon initializer, atau menghapus assertion untuk mendapatkan koleksi.

## R01 — compromise containment

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| R01.1 | Security owner inventarisasi **setiap** trust aktual: JWKS, PEM lokal dan sumber/fallback verifier lain per worker/region; Tester memverifikasi identitas K dan cakupan. | GAP: S1 hanya fake JWKS; inventaris aktual dan rekonsiliasi fallback belum tersedia. |
| R01.2 | Trust admin cabut K dari setiap sumber tersebut; readback independen masing-masing, termasuk cache/refresh yang berlaku. | PARTIAL S1 empty fake JWKS ditolak; tidak ada PEM, verifier lain atau readback trust aktual. |
| R01.3 | Tester catat propagasi yang terukur dan konfirmasi **setiap** worker/region sebelum menyatakan containment. | GAP: butuh observer independen dan data deployment; S1/S2 single-process tidak membuktikan distribusi. |
| R01.4 | Setelah R01.3, old signed K yang belum expired ditolak oleh setiap verifier; ukur status tanpa merekam bearer. | PARTIAL S1 menguji empty JWKS; tidak membuktikan token lama K pada semua verifier. |
| R01.5 | Setelah R01.3, token baru yang dipalsukan menggunakan K dan belum expired juga ditolak pada setiap verifier. | GAP: tidak ada pasangan old/forged K dan verifikasi distribusi pada S1. |
| R01.6 | Negative control: satu verifier/cache sengaja stale masih mempercayai K; sistem pelaporan menyatakan propagasi tidak lengkap dan **tidak** mengklaim containment. | GAP: perlu fixture stale dan observer independen, bukan simulasi yang tersembunyi. |
| R01.7 | Jika penghapusan K tidak dapat dibuktikan untuk suatu jalur, jalur/profile terkait fail closed; rekam hasil tiap jalur. | GAP: mekanisme fail-closed operasional dan aktor yang berwenang belum ditentukan/dibuktikan. |
| R01.8 | Token R dengan profil sah ditolak sebelum R trusted dan diterima hanya setelah trust eksplisit berlaku. | GAP: tidak ada fixture R/konfirmasi trust per verifier pada S1/S2. |

## R02 — operational security/deployment review

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| R02.1 | Security owner menyediakan review ancaman, replay, legacy dan paparan clone; Tester memeriksa cakupan dan kandidat. | GAP: `STEP4-ASSERTION-CROSSWALK-STATIC.md` L257–259 menunjuk kebutuhan, bukan review yang diserahkan; catatan eksternal belum diverifikasi. |
| R02.2 | Security owner menyediakan inventaris verifier dan named incident owner yang bertanggung jawab. | GAP: daftar/nama/penanggung jawab aktual tidak dibuktikan; tidak disimpulkan tidak ada di luar repo. |
| R02.3 | Security owner menyediakan ukuran propagasi serta bukti tersanitasi yang mengikat tiap verifier dan waktu pengukuran. | GAP: rancangan pengukuran bukan hasil atau bukti propagasi. |
| R02.4 | Deployment owner secara terpisah menyediakan inventaris deployment dan rencana rollback sebelum proposal rollout. | GAP: dokumen/test yang dibaca belum membuktikan deliverable owner tersebut. |
| R02.5 | Owner mendisposisikan setiap risiko tersisa secara eksplisit; tanpa itu OPEN. Evidence/review bukan waiver. | GAP: disposition terverifikasi belum tersedia; jangan simpulkan dari acceptance dokumen. |

## K01 — initial trust and compromise response

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| K01.1 | Trust admin buat K sintetis; token K masih valid dengan profil benar diterima **setiap** verifier yang dikonfigurasi. | PARTIAL S1 memvalidasi token dengan fake fetch sebelum variasi, tetapi tidak ada seluruh verifier atau kontrol deployment. |
| K01.2 | Simulasikan kompromi; trust admin menonaktifkan signer K, readback status dan larangan signing di jalur terkait. | GAP: S2 hanya mengganti HS256 secret, tidak membuktikan signer K dinonaktifkan. |
| K01.3 | Hapus K dari JWKS **dan** PEM lokal yang dikonfigurasi secara independen, plus sumber aktual lain; verifikasi masing-masing. | PARTIAL S1 hanya fake JWKS kosong; PEM dan trust aktual belum diuji. |
| K01.4 | Invalidasi/refresh cache yang diizinkan dan distribusikan kunci R yang berbeda; catat operasi dan readback. | GAP: S1 hanya menunjukkan dua fake fetch; tidak membuktikan invalidasi cache aktual atau distribusi R. |
| K01.5 | Selama propagasi Tester dan observer mencatat penerimaan/penolakan dan verifier terakhir, bukan mengasumsikan penolakan instan. | GAP: timestamps/hasil tiap verifier dan observer belum ada. |

## K02 — post-propagation and negative control

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| K02.1 | Observer membuktikan propagasi ke setiap verifier/worker/region dan tidak ada trust K atau fallback yang tersisa sebelum assertion containment. | GAP: cakupan deployment, trust inventory dan observer belum dibuktikan. |
| K02.2 | Old K token belum expired ditolak di setiap verifier setelah K02.1. | PARTIAL S1 empty fake JWKS menolak token; tidak ada bukti distribusi. |
| K02.3 | Newly forged K token belum expired juga ditolak di setiap verifier setelah K02.1. | GAP: pasangan forged dan old token tidak tersedia pada fixture yang dipetakan. |
| K02.4 | R token sah diterima hanya ketika trust R eksplisit sudah efektif; sebelum trust tidak diterima. | GAP: trust dan token R terdistribusi belum ada. |
| K02.5 | Verifier/cache stale masih trust K => propagasi incomplete, tidak boleh lapor containment. | GAP: tidak ada stale distributed negative control yang dipetakan. |
| K02.6 | Bila stale trust tidak dapat dibersihkan, affected path/profile fail closed dan readback menyatakan itu. | GAP: kebijakan dan implementasi operasional fail-closed perlu diputuskan/diverifikasi; tidak disediakan S1. |

## K03 — incident and planned overlap

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| K03.1 | Incident owner menyediakan record redacted berisi issuer terdampak dan deteksi. | GAP: source design hanya meminta record; belum ada record aktual diverifikasi. |
| K03.2 | Record menyertakan waktu dan bukti trust removal, distribusi, serta waktu verifier terakhir. | GAP: belum ada bukti operational yang dipetakan. |
| K03.3 | Record mencakup komunikasi paparan tanpa credential, bearer, private key atau payload rahasia. | GAP: komunikasi dan pemeriksaan redaksi aktual belum ada. |
| K03.4 | Uji normal planned overlap terpisah: old/new diterima hanya pada window disetujui, kemudian old dicabut; jangan mencampur respons kompromi. | GAP: S2 perubahan secret bukan pengujian overlap terencana, expiry atau rollout/rollback. |
| K03.5 | Dalam simulasi kompromi, K tidak sengaja dipertahankan untuk overlap; jangan mengklaim per-token revocation atau batas universal paparan. | GAP: butuh kebijakan dan pemeriksaan operational trust; teks rencana bukan bukti. |

## V09-RT1 — runtime and evidence

Sumber oracle `UAT.md` L439–443; setiap atom di bawah mengacu pada fixture/expected L441 dan bukti/actual L443.

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| V09-RT1.1 | Tester menggunakan image immutable disetujui, Odoo 13 dan interpreter **yang benar-benar mengeksekusi Odoo** melaporkan CPython 3.7.3; catat image digest/ID dan platform. | GAP: Compose L20 memeriksa `python3`, tidak membuktikan interpreter executable Odoo; S7 justru mengharapkan 3.8.20. Tidak ada probe runtime. |
| V09-RT1.2 | Rekam workflow dan selector yang diotorisasi, argv, exit, log tersanitasi, koleksi dan outcome per metode; nol metode => NOT RUN. | GAP: wrapper hanya `compose up` dan menerima nama service, bukan per-case selector tervalidasi; belum ada hasil aktual. |
| V09-RT1.3 | Rekam resolusi **seluruh** dependency dan uji import/API package aktual termasuk PyJWT/cryptography di interpreter Odoo. | GAP: root `requirements.txt` hanya dua direct pins; tidak ada full lock/wheel/system closure atau pengujian API. |
## V09-RT2 — identitas target dan cleanup

Sumber oracle `UAT.md` L445–449: setiap atom V09-RT2.1–V09-RT2.5 memetakan fixture/expected L447 dan kewajiban bukti/actual L449.

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| V09-RT2.1 | Owner menyetujui nama/identitas serta peran Odoo, PostgreSQL, project, network, volume dan database; template names bukan otomatis pilihan final. | GAP: usulan di bawah belum disetujui; Compose service key bukan container identity. |
| V09-RT2.2 | Sebelum mutasi, pemeriksa independen membuktikan target nonproduksi, isolasi dan kepemilikan resource serta nama DB yang tepat; occupancy ambigu => stop. | GAP: wrapper L30–41 menolak project existing tetapi bukan bukti keseluruhan ownership/race fencing. |
| V09-RT2.3 | Binding exact command/selector/dependency ke image/snapshot 3.7.3 yang disetujui, termasuk identitas dan version probe. | GAP: tidak ada command-to-atomic-case final, qualified image atau full lock. |
| V09-RT2.4 | Catat exact ID resource run-owned pada pembuatan dan failure path; hanya itu dibersihkan. | GAP: wrapper `down --volumes --remove-orphans` tidak menginventarisasi/memverifikasi setiap ID sebelum penghapusan. |
| V09-RT2.5 | Independent readback DB dan seluruh exact ID/path setelah cleanup; residu/ketidakpastian dieskalasi, verdict cleanup terpisah. | GAP: wrapper hanya cek exit `down`; tidak ada post-cleanup readback. |
## V09-RT3 — bukti historis dan kompatibilitas

Sumber oracle `UAT.md` L451–455: setiap atom V09-RT3.1–V09-RT3.3 memetakan fixture/expected L453 dan kewajiban bukti/actual L455.

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| V09-RT3.1 | Identifikasi dan preserve evidence asli 3.7.9 beserta kandidat, runtime, actual dan provenance; jangan edit actual. | GAP: v0.9 UAT L3 menyebut historical results, sedangkan v0.8 UAT menyatakan actual NOT RUN; bukti primer dan rekonsiliasi belum ditemukan/dibuktikan. |
| V09-RT3.2 | Tegaskan bukti 3.7.9 historis tidak pernah dilabeli sebagai bukti 3.7.3; pertahankan konflik catatan terbuka. | GAP: source dokumen dipertahankan, tetapi provenance hasil primer dan reconciliation belum diverifikasi. |
| V09-RT3.3 | Klaim kompatibilitas hanya setelah eksekusi 3.7.3 immutable yang disetujui, dependency/API dan hasil dibuktikan. | GAP: target/label/source saja bukan eksekusi; tidak ada klaim kompatibilitas saat ini. |

## G01 dan SCOPE-01 — aggregate dan administrasi

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| G01.1 | Reviewer memastikan dependency separation yang diterima terpisah, tanpa cross-base dependency dan tanpa implicit glue. | PARTIAL S3/S6 hanya source/manifest; keputusan sibling dan installed closures belum dibuktikan. |
| G01.2 | Tester menginstal kedua urutan yang didukung pada DB fresh terpisah, merekam registry dan installed-state readback. | GAP: S3/S6 bukan install; lihat D01 atomic draft untuk kedua urutan dan kesenjangan closure. |
| G01.3 | Tester membuktikan lima provider moves/glue-only API dengan owner dan effective MRO sebenarnya. | PARTIAL S3 AST deklarasi; tidak memverifikasi semua extension atau effective MRO. |
| G01.4 | Tester membuktikan RS independence/API dalam RS-only dan komposisi glue. | PARTIAL S5 memeriksa beberapa stub; nested-only discovery dan closure/MRO/API parity belum dibuktikan. |
| G01.5 | Tester membuktikan URL denial/no bearer pada jalur berlaku, termasuk actor/RPC dan signer/cache observer. | PARTIAL S4 fake `get_access_token` tidak dipanggil; tidak ada native signer/cache, route atau RPC. Exact V10 contract menunggu keputusan. |
| G01.6 | Lead menyertakan seluruh V/U yang berlaku dan hasilnya; jika satu required test blocked, #79 tidak diterima secara normal. | GAP: crosswalk seluruh atomic V/U dan eksekusi belum selesai; parsial bukan acceptance. |
| G01.7 | Reviewer membuktikan tidak ada perubahan sibling feature diam-diam dan memperoleh review/disposisi owner sibling bila diperlukan. | GAP: diff adalah inventaris, bukan keputusan scope/kompatibilitas atau bukti acceptance sibling. |
| SCOPE.1 | Lead membandingkan **semua** path perubahan kumulatif, root/harness/docs/sibling serta staged/unstaged/untracked/ignored yang relevan terhadap baseline dan scope terikat. | PARTIAL: `git diff --name-status -M 2fc50585c5d80dd537535d05679fa5b512b906ef HEAD` kini 90 entries (25 M, 64 A, 1 rename; 91 path sisi rename); ini bukan inventaris dirty/ignored maupun klasifikasi. |
| SCOPE.2 | Owner mendisposisi setiap pengecualian secara eksplisit: terima dengan alasan, pisahkan, atau hapus dengan otorisasi tersendiri. | GAP: disposisi per path dan rekonsiliasi deskripsi PRD/UAT belum diperlihatkan; lihat D01 draft SCOPE.01.b. |
| SCOPE.3 | Lead memverifikasi seluruh disposisi dan rekonsiliasi; tanpa itu SCOPE OPEN dan tidak ada PR. | GAP: tidak ada bukti closure; tidak melakukan PR. |

## Usulan konfigurasi konkret — belum final dan tidak dapat dijalankan sekarang

1. **Envelope:** task `ADDONS13-79`, target source commit `f26a674270467c85b7750073e085e9955e5461e1` sebagai proposal yang butuh rebind; snapshot manifest hash dari commit dan setiap byte yang diizinkan, read-only. UAT hash di atas. Odoo 13 / CPython 3.7.3; PostgreSQL 10; synthetic-only; network internal tanpa host ports; no production, credential hanya reference file/secrets yang dikelola terpisah, tidak ada nilai secret di argumen/log/dokumen. Pengujian tiap urutan/komposisi install butuh DB disposable fresh berbeda, bukan sekadar nama acak.
2. **Identitas usulan:** profile `uat-native`; project `uat-addons13-79-f26a67427046`; Compose service keys `odoo13addonsuat`, `odoo13dbuat`; usulkan database wrapper `odoo13uat`, network Compose `uat-internal`, volume `db-data` dan `odoo-filestore`. Ini service/logical keys, bukan ID/container name yang terverifikasi; Compose project-scoped nama fisik harus di-resolve dan dicatat. Project belum dicek kosong; database sama di tiap disposable instance tidak membuktikan fresh. Owner boleh memilih berbeda, tetapi template/wrapper existing tidak dapat merealisasikan nama database/service alternatif tanpa perubahan ter-review. Ketiadaan persetujuan tidak diperbaiki dengan menggunakan nama contoh historis.
3. **Input image yang ditemukan read-only:** `odoo:13.0` lokal `odoo@sha256:487514270bff6f4a37cfb7532a2f513cfca7ea4ce996f628c6d9edd4502be2a6`, image ID sama, linux/amd64, declared user `odoo`, entrypoint `/entrypoint.sh`, CMD `odoo`, declared volumes `/mnt/extra-addons` dan `/var/lib/odoo`. `postgres:10` lokal `postgres@sha256:b2baf8998630663d21370da06387c950e587071bdd307ee34e661cdcc7442bcc`, image ID sama, linux/amd64, metadata PG 10.21, entrypoint `docker-entrypoint.sh`, volume `/var/lib/postgresql/data`. Metadata bukan bukti interpreter sebenarnya, permissions, startup, secret contract atau dependensi. Final image Odoo task/candidate-specific **belum ada/qualified**; image lama bukan substitusi. Root `Dockerfile` memakai base tersebut namun tidak menyalin `amr_oidc`; `tests/Dockerfile.uat` menyalin source/requirements tapi tidak memasang dependency. Tidak boleh membangun keduanya secara buta.
4. **Dependency/provenance:** `requirements.txt` hanya `PyJWT==2.8.0`, `cryptography==39.0.2`; bukan complete transitive/system/test lock. Diperlukan sumber Odoo exact commit/provenance yang dipercaya, base platform digest, full hash-locked Python wheel + system closure dan artifact offline yang tersedia, serta kebijakan conflict/security; belum tersedia/dibuktikan di sini. Verifikasi final image provenance, source paths, Python patch dan imports/API di executable yang menjalankan Odoo setelah izin. Tidak ada build/pull sekarang.
5. **Batas usulan resource:** usulkan Odoo 2 GiB/1 CPU/256 PID, PostgreSQL 1 GiB/0.5 CPU/128 PID (default konservatif repo skill, bukan approved); tentukan timeout, disk/log, observer dan UID/GID dari metadata final tervalidasi, cek kapasitas host sebelum mutasi. Config dan source read-only; writable mounts dibatasi; verify image-declared volumes dan mount list sebelum start, tanpa anonymous volume tidak tercatat. `PASSWORD_FILE` pada Compose bukan bukti Odoo entrypoint mendukungnya: verifikasi kontrak file secret dan user nonroot tanpa menampilkan nilainya; jika gagal STOP.
6. **Command dan selector:** repository mewajibkan `tests/run-uat.sh` sebagai launch path untuk Compose; wrapper memanggil `docker compose ... up --abort-on-container-exit --exit-code-from "$1" "$@"`, dan parameter adalah service names, bukan test IDs. Native helper `skills/odoo-integration-test/scripts/run_integration.py` mewajibkan `--odoo-bin`, `--database`, `--addon`, `--mode install|update`, `--ack-test-db`; ia membentuk `-d DB -i|-u ADDON --test-tags=/ADDON --stop-after-init` dan memanggil file dengan `sys.executable`; `--dry-run` memerlukan `shlex.join`, tidak ada di Python 3.7. Selector ini per addon, bukan pemetaan 10 kasus yang cukup. Kebutuhan: tentukan exact argv per komposisi dan tiap case/fixture, native discovery Odoo, full methods/expected count dan unit runner `skills/odoo-unit-test/scripts/run_tests.py --addon ...`; reconcile native dan offline tanpa duplikasi. Jika controller versi Python lebih baru, adapter test-only yang direview harus memanggil executable Odoo 3.7.3 di service dan merekam nested argv/exit; integrasi helper ke wrapper/Compose **belum ada**, jangan bypass wrapper atau menganggap adapter sudah berfungsi. Gabungan `--database` Compose, runner database dan install-order commands harus ditinjau agar tidak konflik. Tidak ada executable command yang layak diserahkan sebagai final sebelum seam itu diselesaikan.
7. **Ledger/fencing:** gen2 existing dipertahankan; verifikasi sumber otoritatif, binding, count, sisa budget dan izin sebelum tindakan; tidak reset dan tidak mengasumsikan 3 attempt tersedia. Wrapper mensyaratkan cap tepat 3, `odoo13uat`, exact Compose path dan runtime string; bila file ledger tidak ada ia menginisialisasi `count=0`, sehingga berbahaya untuk gen2 yang belum dibuktikan. Lock L28–52 dilepas sebelum `up`; numeric file tidak mengikat generation/candidate/target dan tidak menyediakan lease/fencing sepanjang lifecycle. Butuh desain ter-review dengan lock atomik, durable reservation, binding terautentikasi, validasi occupancy/ownership dan recovery interrupted; setiap error/ambiguity => STOP sebelum side effect. Jangan memodifikasi ledger dalam persiapan ini.
8. **Freshness dan readiness tanpa fake:** Compose L56 otomatis membuat `odoo13uat` saat inisialisasi PostgreSQL; catalog check sesudah itu **tidak** membuktikan sebelumnya absent. `pg_isready` L65–69 tidak membuktikan query autentik berhasil pada final server. Desain future ter-review harus menolak existing project/resources, membuktikan volume run-owned benar-benar kosong sebelum init, memulai instance PostgreSQL isolated yang hanya membuat maintenance DB, melakukan query katalog autentik untuk exact nama test DB dan merekam nol row **sebelum** membuatnya; baru create dalam instance milik run, lalu lakukan beberapa query autentik berturut-turut pada target yang tepat setelah final-server startup, dengan timeout dan kegagalan closed. Jangan menggunakan fake SQL, unique name, mock DB, atau hanya isready. Protokol ini tidak dapat dipasang pada Compose/wrapper sekarang tanpa perubahan/integrasi yang diotorisasi dan diuji; jangan meluncurkan sequence alternatif di luar wrapper.
9. **Independent observer:** selain membatasi network, instrumentasikan client/transport dan process/socket termasuk native/child/resolver pada keseluruhan klasifikasi, key/JWKS, sukses, error dan unavailable provider. Rekam percobaan self-provider/introspection tanpa bearer; bedakan remote/frontchannel sah. Kalibrasi observer dengan positive known request dan clean control dalam setup berizin terpisah; blind spot atau positive control gagal => PARTIAL/BLOCKED, bukan zero traffic PASS. Untuk K/R ukur setiap verifier/worker/region dengan jam dan identitas yang dapat direkonsiliasi, tidak menyimpulkan global dari synthetic single instance.
10. **Evidence/cleanup:** catat manifest, approvals, selector, result per method, image/runtime, sanitized observations serta ownership ID incremental ke lokasi persisten mode terbatas; raw log dianggap sensitif. Saat setiap exit/failure, simpan output sebelum container hilang, buktikan fencing/ownership, drop hanya DB run-owned lalu authenticated catalog readback absent selagi PostgreSQL hidup, hapus hanya recorded containers/network/volumes/images/config/secret milik run, lalu independen inspect setiap ID/path absent; tidak gunakan prune atau sentuh resources shared. SIGKILL/host failure butuh recovery berbasis daftar ID, bukan tebakan nama. Cleanup gagal/tidak dapat diverifikasi => HOLD/eskalasi terpisah dari hasil fungsional. Existing wrapper down saja tidak melakukan DB catalog/readback atau independent exact-ID readback.

## Hitungan dan blockers

- Slice ini **10 case ID**: R01–R02 (2), K01–K03 (3), V09-RT1–RT3 (3), G01 (1), SCOPE-01 (1). Terdapat **50 atom unik**: R01 8, R02 5, K01 5, K02 6, K03 5, RT1 3, RT2 5, RT3 3, G01 7, SCOPE 3; **10 PARTIAL dan 40 GAP**, sehingga seluruh 50 belum memiliki bukti memadai. Seluruhnya **actual NOT RUN**, tidak ada full-case PASS. Atom adalah unit analisis dokumen, bukan jumlah native test atau hasil coverage seluruh 82 lineage cases; lihat row IDs di atas.
- Blocker lintas slice: (1) rebind kandidat/snapshot dan persetujuan final config serta izin build/container/DB/test yang masih terpisah; (2) SCOPE dan keputusan fresh mapping/profile, lifecycle/route serta risk/compatibility yang berlaku; (3) exact Odoo source/image provenance, full offline dependency/system lock dan actual 3.7.3 API qualification; (4) discovery dan exact per-case selector/fixtures belum lengkap; (5) wrapper-integrated freshness, readiness, secret contract, fencing/ledger gen2 dan cleanup/readback belum diimplementasikan atau diverifikasi; (6) observer terkalibrasi dan distributed trust/propagation evidence; (7) security/deployment/incident owner deliverables dan historical 3.7.9 reconciliation. Ini **tujuh kelompok blocker**, bukan klaim hanya tujuh atom tersisa atau bahwa semua memerlukan keputusan Owner. Setiap gap dalam tabel tetap terbuka; beberapa dapat diselesaikan melalui kerja teknis/review, bukan keputusan Owner.
- Final gate: semua input di atas dan run-owned isolation harus dibuktikan; persetujuan dokumen atau rancangan bukan authorization untuk mencoba runtime. G01 tidak dapat dinyatakan lulus dari subset ini; SCOPE-01 tetap OPEN.


## Rekonsiliasi evidence Gen5 — diagnostik, bukan rebind atau acceptance

**Binding dan batas:** UAT diterima sesuai metadata, byte SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; isi internal `actual NOT RUN` dipertahankan. Evidence Gen5 menunjuk kandidat `49b5a739ce25b8feeb74b8d7c91641e2c98c5978`, bukan HEAD saat pemeriksaan `5f1f0f9433f723f850df8640fdc1db261476df91`; tidak ada rebind yang disimpulkan. Tidak ada rerun pada rekonsiliasi ini. Kesepuluh kasus **FULL CASE NOT ESTABLISHED**; SCOPE-01 **OPEN**. Tabel lama adalah penilaian statis historis, bukan status actual terbaru.

Evidence sementara: `/home/ubuntu/.hermes/profiles/lead/cache/scratch/addons13-79-gen5-preflight/safe-summary.json` SHA-256 `50c8f26e3082b6c3c5a3d6141e7e296cb856e801248a4f9b84a22a4223b0791d`; scratch bisa terhapus, bukan arsip permanen. Referensi `controller` dan `raw_log_restricted` di JSON: restricted, jangan salin bearer, credential, key, payload atau SQL mentah. Hash raw terverifikasi: resource `5b836a4210aa71165d9323e52eb60ac6298f5d4fa1ea65c41ff46ff64fb73185`; glue `d3d8a093dd1f4b43ed812e57c6533acdded185be1e43a23a67c6047c7ec4a312`; provider `fe5ab1919312979b9df7ce468bb531ef5cfa3aae601ab22cb25a5bdc54c19b5d`. Controller hash masing-masing `e02206022df4b3513e32c2b82dd2ceb085376cbae6d667383ca5ba17cc597628`, `661b9ef32031fa86f80054b42a645b0727612eab2275df1e7cedeb6385704430`, `1553ac8399ac9f1176038093afaec8076681252320f2a29fcf87a884c121f727`.

Tiga selector `amr_resource`, `amr_oidc_resource`, `amr_oidc`: exit 0, start unik 28/18/44 dan ringkasan modul bertotal sama 28/18/44, tanpa test failure yang tercatat; 90 metode, bukan 90 kasus UAT. Raw SQL ERROR masing-masing 3/0/6, sehingga exit 0 bukan klaim log bersih. Log Odoo 13.0-20221005; controller mengukur `python3` 3.7.3 dan PyJWT 2.8.0 dalam container serta PostgreSQL 10.21; probe terpisah itu sendiri bukan pembuktian seluruh closure/API atau interpreter executable Odoo. Provider memakai proxy mode; header proxy bukan TLS nyata. Tidak ada observer egress lengkap/terkalibrasi, sehingga isolasi tidak membuktikan nol percobaan. Tidak ada interpretasi target deployment penuh.

Readback pascarun berbeda dari cleanup: resource `amr_resource:installed`; glue ketiga addon installed; provider `amr_oidc:installed`, dua lainnya `uninstalled` (bukan tidak ada di addons path). Controller melaporkan catalog pre-create dan post-drop 0 serta exact container/network absent; ini bukti terbatas cleanup yang dicatat, bukan verdict fungsional atau jaminan semua path/volume di luar daftar. Snapshot post-run cocok menurut controller. Kedua urutan instalasi tidak terbukti oleh tiga selector ini.

**Kode evidence:** `D1` diagnostik lokal dari `amr_oidc_resource/tests/integration/test_user_token_glue.py` pada commit Gen5, `test_signing_configuration_change_uses_new_key_and_ttl` L112–127: assertion exp fixed+120 dan audience token HS256 baru, serta `InvalidSignatureError` token lama dengan secret baru; `test_signing_key_removal_after_warm_issuance_rejects` L105–110 mengharapkan `ValueError` setelah parameter secret dikosongkan. Keduanya tercatat mulai dalam selector glue dan ringkasan 8 metode tanpa failure; hanya perubahan secret lokal, bukan incident K RSA atau trust propagation. `D2` `amr_oidc/tests/integration/test_public_key_orm.py::TestPublicKeyORM::test_rsa_ec_jwks_active_signing_and_public_only` L128–157: assert set kid JWKS hanya record aktif, metadata dan tidak ada komponen privat; dimulai dan termasuk ringkasan provider tanpa failure. Ini ORM JWKS satu instance, bukan pencabutan trust di semua verifier. `D3` `amr_resource/tests/integration/test_contracts.py::TestResourceContracts::test_ut08_user_predicates_environment_and_stubs` L170–195: `get_access_token`/`create_access_token` raise `UserError`, tiga URL wrapper mengembalikan input di fixture RS; dimulai dan termasuk ringkasan resource tanpa failure. Ini bukan seluruh API/komposisi. Assertion aktif dibandingkan via `git show 49b5a739ce25b8feeb74b8d7c91641e2c98c5978:<path>`. `S` berarti statis historis S1–S7 di atas, bukan hasil unit; `NA` NOT ASSESSED oleh evidence yang dipetakan. D1–D3 adalah diagnostic slice, bukan PASS atom lengkap.

| Case / atom | Rekonsiliasi Gen5 terhadap expected UAT lengkap |
|---|---|
| R01.1 | NA: inventaris seluruh trust/worker/region belum ada; S1 hanya fake JWKS. |
| R01.2 | D2 hanya eksklusi record JWKS inactive lokal; penghapusan K dari JWKS, PEM dan sumber lain serta readback masing-masing belum dibuktikan. |
| R01.3 | NA: pengukuran propagasi tiap worker/region. |
| R01.4 | D1 hanya token lama HS256 dengan secret baru; penolakan K RSA di seluruh verifier pascapropagasi tidak dibuktikan. |
| R01.5 | NA: forged K yang belum expired dan seluruh verifier. |
| R01.6 | NA: stale verifier sebagai negative control containment. |
| R01.7 | NA: fail-closed affected path bila removal tidak terverifikasi. |
| R01.8 | NA: R sebelum/sesudah trust eksplisit. |
| R02.1 | NA: review threat/replay/legacy/clone security owner. |
| R02.2 | NA: inventaris verifier dan named incident owner. |
| R02.3 | NA: ukuran propagasi dan bukti redacted per verifier. |
| R02.4 | NA: deployment inventory dan rollback terpisah. |
| R02.5 | NA: disposisi risiko eksplisit Owner; acceptance spesifikasi bukan waiver. |
| K01.1 | NA: K RSA diterima setiap verifier; S1 hanya fake fixture. |
| K01.2 | D1 secret dikosongkan setelah warm issuance; tidak membuktikan disable signer K kompromi di semua jalur. |
| K01.3 | D2 hanya JWKS ORM record aktif; tidak membuktikan trust PEM independen atau removal semua sumber. |
| K01.4 | S1 fake fetch saja; invalidasi cache aktual dan distribusi R NA. |
| K01.5 | NA: observasi penerimaan selama propagasi dan verifier terakhir. |
| K02.1 | NA: konfirmasi tiap verifier/worker/region dan fallback. |
| K02.2 | D1 verifikasi secret baru lokal saja; tidak membuktikan old K RSA ditolak tiap verifier. |
| K02.3 | NA: newly forged K tidak expired. |
| K02.4 | NA: R hanya diterima setelah trust eksplisit. |
| K02.5 | NA: stale verifier/cache mencegah klaim containment. |
| K02.6 | NA: fail-closed affected path bila tidak dapat dibersihkan. |
| K03.1 | NA: record incident issuer/deteksi. |
| K03.2 | NA: waktu removal/distribution/last verifier. |
| K03.3 | NA: redaksi komunikasi paparan. |
| K03.4 | D1 bukan tes planned overlap lama/baru dan window terpisah. |
| K03.5 | NA: kebijakan tidak mempertahankan K kompromi untuk overlap dan batas klaim revocation. |
| V09-RT1.1 | Diagnostik: versi Odoo pada raw, python3 3.7.3 pada controller; binding executable, image immutable disetujui dan platform lengkap belum dibuktikan di sini. |
| V09-RT1.2 | Diagnostik: tiga command/exit, log, start dan ringkasan dihitung; pemetaan selector ke seluruh expected case dan otorisasi target lengkap belum dibuktikan. |
| V09-RT1.3 | Diagnostik: import PyJWT 2.8.0; full dependency resolution dan seluruh API termasuk cryptography belum dibuktikan. |
| V09-RT2.1 | Controller mencatat identitas resource run; persetujuan konfigurasi final seluruh nama/peran tidak dibuktikan di sini. |
| V09-RT2.2 | Controller mencatat network, mounts dan katalog pre-create 0; persetujuan/independent verification seluruh isolation dan ownership sebelum mutasi tidak disimpulkan. |
| V09-RT2.3 | Snapshot manifest dan command dicatat; binding semua dependency/selector/image ke target yang disetujui serta rebind HEAD belum dibuktikan. |
| V09-RT2.4 | Controller mencatat ID network dan dua container; kelengkapan inventaris semua failure path dan seluruh resources NA. |
| V09-RT2.5 | Controller mencatat catalog post-drop 0 dan tiga ID absent; tidak membuktikan seluruh ID/path/volume di luar readback yang tercatat. Cleanup terpisah dari hasil test. |
| V09-RT3.1 | S historis saja; evidence primer 3.7.9 dan actual aslinya belum direkonsiliasi. |
| V09-RT3.2 | NA: provenance perbedaan actual 3.7.9 tetap terbuka; jangan relabel sebagai 3.7.3. |
| V09-RT3.3 | Diagnostik versi/run bukan kualifikasi full dependency, acceptance runtime atau compatibility target. |
| G01.1 | S3/S6 static manifest; pemisahan dependency terima dan semua installed closures belum terbukti. |
| G01.2 | Readback tiga komposisi di atas; kedua supported install orders fresh dan hasil lengkap belum terbukti. |
| G01.3 | S3 static deklarasi; effective MRO dan seluruh lima owner di semua extension NA. |
| G01.4 | D3 direct denial dan URL passthrough RS fixture; RS-only dan glue API parity penuh serta closure/MRO NA. |
| G01.5 | D3 RS passthrough bukan glue denial; S4 hanya offline mock, signer/cache/RPC/route lengkap NA dan exact V10 pending. |
| G01.6 | NA: seluruh V/U berlaku dan semua gate; tiga selector tidak membuktikan G01. |
| G01.7 | NA: sibling owner review dan tidak ada silent modification. |
| SCOPE.1 | S historis inventaris diff terbatas pada f26, bukan inventaris kumulatif current termasuk dirty/ignored. |
| SCOPE.2 | NA: disposisi Owner setiap pengecualian dan rekonsiliasi scope/diff. |
| SCOPE.3 | NA: verifikasi semua disposisi; **OPEN, tidak ada PR**. |

**Hitungan:** 10 case (2 R, 3 K, 3 RT, G01, SCOPE-01), 50 atom (8+5+5+6+5+3+5+3+7+3). Semua 10 full case NOT ESTABLISHED; status bukti pada tiap atom di atas tidak mengubah angka historis 10 PARTIAL/40 GAP yang dihitung dari statis f26. Gaps utama: trust/incident terdistribusi dan owner deliverables, full runtime/dependency dan observer, kedua install order/API efektif, scope dan rebind. Tidak ada klaim kasus lulus atau waiver.

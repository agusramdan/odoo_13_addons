# ADDONS13-79 Step 4 — crosswalk R/K/runtime

> **DRAFT SANITIZED DERIVATIVE — NOT ACCEPTED.** Turunan publik untuk review; bukan dokumen acceptance, rebind, waiver, izin runtime, atau full UAT PASS. SCOPE-01 **OPEN**. Evidence Gen5 hanya diagnostik parsial pada kandidat `49b5a739ce25b8feeb74b8d7c91641e2c98c5978`, bukan HEAD `5f1f0f9433f723f850df8640fdc1db261476df91`. Review independen lengkap atas redaksi dan kesetiaan wajib sebelum publikasi.

> **Batas waktu:** bagian historis sampai `Hitungan dan blockers` adalah desain statis pada `f26a674270467c85b7750073e085e9955e5461e1`; actual UAT **NOT RUN pada saat itu**. Rekonsiliasi Gen5 sesudahnya dicatat terpisah di akhir; tidak mengganti atau mengubah historical actual tersebut.

**STATIC DESIGN ONLY — seluruh actual UAT NOT RUN.** Tidak ada database, container, build/pull, integration test, UAT, atau suite dijalankan. Dokumen ini bukan konfigurasi final, rebind, waiver, approval scope, bukti propagasi, ataupun implementasi harness. `UAT.md` SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; Metadata acceptance mencatat persetujuan spesifikasi; batas rujukan sumber internal tidak dipublikasikan. Identitas analisis statis adalah commit `f26a674270467c85b7750073e085e9955e5461e1`; rebind sebelumnya merujuk commit `0ebf9ac745450b9b3f0555829490b3c3b0978f79` dan tidak otomatis berlaku untuk kandidat lain. Draft D01 tetap menjadi rincian D01; dokumen ini tidak mengklaim melengkapi semua keluarga lain. SCOPE-01 OPEN; keputusan fresh mapping/profile, route-helper, lifecycle, acceptance risiko dan waiver terpisah tetap belum diputuskan oleh persetujuan spesifikasi.

## Cara membaca crosswalk

Setiap baris adalah observable atomik untuk sepuluh ID yang diminta; beberapa ID sengaja berbagi observable, bukan deduplikasi kasus. **GAP** = belum ada assert/rekaman memadai yang ditemukan pada sumber terbatas ini; bukan klaim tidak ada di seluruh dunia. **PARTIAL** = assert spesifik ada dalam source, namun tidak memenuhi seluruh observable atau batasnya. Tidak satu pun label berarti test dikoleksi atau lulus. Actor dan fixture berikut bersifat synthetic nonproduksi; security owner, deployment owner, incident owner, trust admin dan Tester masing-masing adalah peran berbeda, bukan fiktif yang dianggap sudah ditunjuk. Untuk rotation gunakan K dan R RSA sintetis berbeda, token K lama dan token K baru yang dipalsukan setelah kompromi, keduanya belum expired; trust JWKS dan local PEM dikonfigurasi independen; inventaris verifier/worker/region yang sebenarnya harus disetujui dan dibuktikan, bukan satu fixture DB dianggap global. Isolasi jaringan bukan observer percobaan jaringan.

## Referensi statis tersanitasi

S1: unit offline fake JWKS menguji dua validasi, rejection JWKS kosong/duplikat atau metadata salah; bukan bukti incident, PEM, distribusi, atau forged token. S2: test integrasi perubahan signing secret lokal; discovery native NOT RUN, bukan removal trust terdistribusi. S3: unit offline manifest/deklarasi glue, bukan registry/MRO. S4: unit offline kedua URL helper menolak pembuatan bearer dan tidak memanggil penerbitan; bukan RPC/route/signer/cache atau runtime MRO. S5: fixture ORM menolak direct issuance dan meneruskan URL; native discovery NOT RUN. S6: unit offline manifest provider, bukan install/closure. S7: assertion historis Python 3.8.20, bukan pengukuran runtime 3.7.3. Nama dan lokasi test **REDACTED**. Discovery statis bukan bukti koleksi; jangan melemahkan guard atau assertion demi koleksi.

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

Keterkaitan kasus dan atom V/U: [crosswalk V/U](STEP4-CROSSWALK-VU.md). K01 dan V09-RT1 pada dokumen ini tetap gate terpisah; rujukan silang tidak membuktikan hasil.

| Atom | Actor / fixture dan assertion yang harus diamati | Source / gap dan discovery |
|---|---|---|
| G01.1 | Reviewer memastikan dependency separation yang diterima terpisah, tanpa cross-base dependency dan tanpa implicit glue. | PARTIAL S3/S6 hanya source/manifest; keputusan sibling dan installed closures belum dibuktikan. |
| G01.2 | Tester menginstal kedua urutan yang didukung pada DB fresh terpisah, merekam registry dan installed-state readback. | GAP: S3/S6 bukan install; lihat D01 atomic draft untuk kedua urutan dan kesenjangan closure. |
| G01.3 | Tester membuktikan lima provider moves/glue-only API dengan owner dan effective MRO sebenarnya. | PARTIAL S3 AST deklarasi; tidak memverifikasi semua extension atau effective MRO. |
| G01.4 | Tester membuktikan RS independence/API dalam RS-only dan komposisi glue. | PARTIAL S5 memeriksa beberapa stub; nested-only discovery dan closure/MRO/API parity belum dibuktikan. |
| G01.5 | Tester membuktikan URL denial/no bearer pada jalur berlaku, termasuk actor/RPC dan signer/cache observer. | PARTIAL S4 fake `get_access_token` tidak dipanggil; tidak ada native signer/cache, route atau RPC. Exact V10 contract menunggu keputusan. |
| G01.6 | Lead menyertakan seluruh V/U yang berlaku dan hasilnya; jika satu required test blocked, #79 tidak diterima secara normal. | GAP: crosswalk seluruh atomic V/U dan eksekusi belum selesai; parsial bukan acceptance. |
| G01.7 | Reviewer membuktikan tidak ada perubahan sibling feature diam-diam dan memperoleh review/disposisi owner sibling bila diperlukan. | GAP: diff adalah inventaris, bukan keputusan scope/kompatibilitas atau bukti acceptance sibling. |
| SCOPE.1 | Lead membandingkan **semua** path perubahan kumulatif, root/harness/docs/sibling serta staged/unstaged/untracked/ignored yang relevan terhadap baseline dan scope terikat. | PARTIAL: inventaris historis 90 entries (25 M, 64 A, 1 rename; 91 path sisi rename); bukan inventaris dirty/ignored maupun klasifikasi. Command dan penargetan **REDACTED**. |
| SCOPE.2 | Owner mendisposisi setiap pengecualian secara eksplisit: terima dengan alasan, pisahkan, atau hapus dengan otorisasi tersendiri. | GAP: disposisi per path dan rekonsiliasi deskripsi PRD/UAT belum diperlihatkan; lihat D01 draft SCOPE.01.b. |
| SCOPE.3 | Lead memverifikasi seluruh disposisi dan rekonsiliasi; tanpa itu SCOPE OPEN dan tidak ada PR. | GAP: tidak ada bukti closure; tidak melakukan PR. |

## Persyaratan envelope dan harness — rincian penargetan REDACTED

Usulan belum final atau dapat dijalankan. Perlukan persetujuan kandidat/snapshot dan envelope terikat, lingkungan nonproduksi terisolasi, image immutable dan provenance, interpreter aktual, dependency closure dan API, serta secret yang dikelola tanpa menampilkan nilainya. Identitas dan alokasi resource konkret **REDACTED / NOT ASSESSED** dalam turunan publik.

Sebelum izin eksekusi diperlukan command dan selector terikat per kasus/komposisi, discovery tervalidasi, kontrol resource dan secret, ledger yang tidak direset, atomic fencing/ownership serta recovery; ketidakpastian harus STOP sebelum side effect. Freshness database harus dibuktikan sebelum pembuatan, readiness melalui query autentik pada target yang benar, bukan sekadar mock atau health check. Harness terintegrasi belum dibuktikan.

Observer independen dan terkalibrasi harus mencakup proses, transport dan resolver serta positive/clean controls; isolasi jaringan saja bukan bukti nol percobaan. Ukur propagasi di setiap verifier/worker/region. Evidence disanitasi dan disimpan dengan kontrol akses; cleanup hanya resource milik run yang tercatat, dengan readback independen dan eskalasi terpisah bila gagal atau tidak pasti.

## Hitungan dan blockers

- Slice ini **10 case ID**: R01–R02 (2), K01–K03 (3), V09-RT1–RT3 (3), G01 (1), SCOPE-01 (1). Terdapat **50 atom unik**: R01 8, R02 5, K01 5, K02 6, K03 5, RT1 3, RT2 5, RT3 3, G01 7, SCOPE 3; **10 PARTIAL dan 40 GAP**, sehingga seluruh 50 belum memiliki bukti memadai. Seluruhnya **actual NOT RUN**, tidak ada full-case PASS. Atom adalah unit analisis dokumen, bukan jumlah native test atau hasil coverage seluruh 82 lineage cases; lihat row IDs di atas.
- Blocker lintas slice: (1) rebind kandidat/snapshot dan persetujuan final config serta izin build/container/DB/test yang masih terpisah; (2) SCOPE dan keputusan fresh mapping/profile, lifecycle/route serta risk/compatibility yang berlaku; (3) exact Odoo source/image provenance, full offline dependency/system lock dan actual 3.7.3 API qualification; (4) discovery dan exact per-case selector/fixtures belum lengkap; (5) wrapper-integrated freshness, readiness, secret contract, fencing/ledger gen2 dan cleanup/readback belum diimplementasikan atau diverifikasi; (6) observer terkalibrasi dan distributed trust/propagation evidence; (7) security/deployment/incident owner deliverables dan historical 3.7.9 reconciliation. Ini **tujuh kelompok blocker**, bukan klaim hanya tujuh atom tersisa atau bahwa semua memerlukan keputusan Owner. Setiap gap dalam tabel tetap terbuka; beberapa dapat diselesaikan melalui kerja teknis/review, bukan keputusan Owner.
- Final gate: semua input di atas dan run-owned isolation harus dibuktikan; persetujuan dokumen atau rancangan bukan authorization untuk mencoba runtime. G01 tidak dapat dinyatakan lulus dari subset ini; SCOPE-01 tetap OPEN.


## Rekonsiliasi evidence Gen5 — diagnostik, bukan rebind atau acceptance

**Binding dan batas:** UAT diterima sesuai metadata, byte SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; isi internal `actual NOT RUN` dipertahankan. Evidence Gen5 menunjuk kandidat `49b5a739ce25b8feeb74b8d7c91641e2c98c5978`, bukan HEAD saat pemeriksaan `5f1f0f9433f723f850df8640fdc1db261476df91`; tidak ada rebind yang disimpulkan. Tidak ada rerun pada rekonsiliasi ini. Kesepuluh kasus **FULL CASE NOT ESTABLISHED**; SCOPE-01 **OPEN**. Tabel lama adalah penilaian statis historis, bukan status actual terbaru.

Evidence Gen5 berasal dari ringkasan sementara dan log terbatas; lokasi, identitas internal dan hash log **REDACTED**. Jangan publikasikan bearer, credential, key, payload atau SQL mentah.

Ringkasan sementara privat mencatat tiga selector diagnostik dan probe terpisah: `python3` 3.7.3 dan PyJWT 2.8.0 dalam container serta PostgreSQL 10.21. Identitas selector dan sumber mentah tidak dipublikasikan; pernyataan ini adalah laporan historis, bukan bukti primer yang dapat diaudit secara publik. Probe terpisah itu sendiri bukan pembuktian seluruh closure/API atau interpreter executable Odoo. Provider memakai proxy mode; header proxy bukan TLS nyata. Tidak ada observer egress lengkap/terkalibrasi, sehingga isolasi tidak membuktikan nol percobaan. Tidak ada interpretasi target deployment penuh.

Readback pascarun berbeda dari cleanup: ringkasan privat melaporkan satu komposisi RS terpasang, komposisi glue dengan tiga addon terpasang, serta komposisi provider dengan dua addon lain uninstalled (bukan berarti tidak ada pada addons path). Controller melaporkan catalog pre-create dan post-drop 0 serta exact container/network absent; ini bukti terbatas cleanup yang dicatat, bukan verdict fungsional atau jaminan semua path/volume di luar daftar. Snapshot post-run cocok menurut controller. Kedua urutan instalasi tidak terbukti oleh tiga selector ini.

**Kode evidence:** D1 diagnostik lokal perubahan signing secret dan penolakan issuance setelah secret dihapus; bukan incident K RSA atau propagasi trust. D2 diagnostik ORM satu instance: JWKS hanya record aktif, metadata, tanpa komponen privat; bukan removal trust seluruh verifier. D3 diagnostik fixture RS: direct issuance ditolak dan URL passthrough; bukan seluruh API/komposisi. Lokasi dan identitas test **REDACTED**. S = statis historis S1–S7, bukan hasil unit; NA = NOT ASSESSED. D1–D3 bukan PASS atom lengkap.

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

# Panduan User — Service Client

## Ruang lingkup dan batas panduan

Service Client adalah addon client HTTP/JSON-RPC untuk Odoo 13 menuju layanan seperti amr_resource; bukan penyedia login/IdP dan bukan resource server. Panduan ini berdasarkan pembacaan sumber saja. Seluruh menu, tampilan, ACL, registry, wizard dan alur berikut **belum diverifikasi pada runtime Odoo 13**. Pembacaan sumber tidak membuktikan koneksi, keberhasilan autentikasi, replay, atau penerimaan server nyata.

Penggunaan dibatasi untuk development/demo, bukan produksi. Panduan ini tidak membuktikan keamanan atau kompatibilitas runtime dan tidak memberi izin operasi layanan nyata.

Untuk rincian teknis, lihat [panduan developer](developer.md); contoh aman hanya [metadata sintetis](examples/service-client-demo.json), bukan file import Odoo.

## Peran, menu dan hak akses

XML mendeklarasikan menu Integration di bawah parent teknis base.menu_users, dengan Endpoints, Credentials, Client, Integration Log. Semuanya memakai base.group_no_one. Jangan menganggap posisi visual menu dalam instalasi tertentu telah terverifikasi; menu yang tidak terlihat bukan bukti akses ORM/RPC ditolak. Referensi: `amr_service_client/views/menuitem.xml:3`.

| Peran/grup deklaratif | Hak menurut ACL lokal | Batas |
|---|---|---|
| Internal user / base.group_user | Read pada Endpoint, Credential, Client, Payload, Integration Log | Read tidak berarti hanya data aman; kerahasiaan field dan isolasi company belum terbukti |
| ERP manager / base.group_erp_manager | Create/read/write/delete pada lima model persistent tersebut | Bukan izin otomatis dari owner untuk operasi live |
| Internal user pada kedua wizard | Create/read/write/delete wizard | Visibility tombol/menu bukan proteksi ORM |
| base.group_no_one | Grup pada deklarasi menu teknis | Bukan pengganti ACL dan bukan jaminan isolasi |

Referensi: `amr_service_client/security/ir.model.access.csv:2`, `amr_service_client/security/ir.model.access.csv:17`. Hak efektif gabungan core/dependency/record rules, company, field secret dan UI **belum diverifikasi pada runtime Odoo 13**. Jangan menyimpan credential nyata dengan asumsi label password/teknis atau menu tersembunyi membuatnya terlindungi.

## Persiapan sebelum konfigurasi

Manifest mendeklarasikan versi 13.0.0.1.0, dependency base/web/base_setup/amr_resource dan Python pyjwt; ini bukan hasil instalasi sukses (`amr_service_client/__manifest__.py:6`). Administrator harus memperoleh izin lingkungan dan rencana keamanan sebelum instalasi atau konfigurasi nyata. Panduan ini bukan instruksi instalasi atau izin mengubah DB maupun membuka layanan.

Siapkan rencana endpoint yang diotorisasi, kontrak HTTP/JSON-RPC, model yang sesuai, siapa penulis action tepercaya, dan cara menangani data sensitif. HTTPS, allowlist host, validasi scope, sandbox kode dan isolasi tenant tidak boleh diasumsikan tersedia. Jangan mengisi credential riil untuk mencoba panduan ini.

## Alur konfigurasi: Endpoint → Credential → Service Client → server action

Langkah di bawah adalah penjelasan deklarasi sumber, bukan instruksi menjalankan operasi pada lingkungan saat ini. Semuanya **belum diverifikasi pada runtime Odoo 13**.

### 1. Endpoint

View Endpoints menampilkan name/code/url/audience/credential/timeout/active. Form mempunyai Test Connection dan tab Endpoint, Authentication, Help. Isi name dan code (wajib); pilih Source Value, Base Url atau nama config parameter, base_path, audience, timeout, Content-Type, active_log dan credential pada tab Authentication sesuai rencana yang sudah disetujui. Referensi: `amr_service_client/views/service_endpoint_views.xml:9`, `amr_service_client/views/service_endpoint_views.xml:26`, `amr_service_client/views/service_endpoint_views.xml:50`, `amr_service_client/views/service_endpoint_views.xml:72`.

Source URL value memakai isian langsung; env mengambil environment berdasarkan nama, config dari config Odoo, config_parameter dari System Parameter. Edit pada System Parameter dapat membuat parameter melalui sudo, bukan sekadar membuka data read-only. Jangan mengubah parameter tanpa izin. Referensi: `amr_service_client/models/service_endpoint.py:20`, `amr_service_client/models/service_endpoint.py:44`, `amr_service_client/models/service_endpoint.py:69`.

code bukan unique yang ditegakkan source walaupun teks Help menyebut unique. Timeout default 30. Path relatif mengikuti base_path, path '/' atau kosong menggunakan host, path berawalan '/' melewati base_path. URL/HTTPS/host tidak divalidasi allowlist lokal. Header default text/plain dan Accept application/json meskipun payload dikirim dengan json. Referensi: `amr_service_client/models/service_endpoint.py:105`, `amr_service_client/models/service_endpoint.py:128`, `amr_service_client/models/service_endpoint.py:168`.

### 2. Credential

Form Credentials menyediakan name/source/scopes/reference serta tab JSON untuk database, tombol Config Credential dan Test Credential. Reference ditampilkan/wajib pada view untuk sumber selain database. Referensi: `amr_service_client/views/service_credential_views.xml:23`, `amr_service_client/views/service_credential_views.xml:36`, `amr_service_client/views/service_credential_views.xml:56`.

| Sumber Credential | Makna reference/data menurut sumber |
|---|---|
| database | JSON pada record credential |
| file_path | Path file JSON |
| env_json | Nama environment berisi JSON |
| env_path | Nama environment berisi path file JSON |
| config_path | Nama key konfigurasi Odoo berisi path file JSON |
| system_parameter_json | Nama System Parameter berisi JSON |
| system_parameter_path | Nama System Parameter berisi path file JSON |

Referensi: `amr_service_client/models/service_credential.py:16`, `amr_service_client/services/credential_loader.py:12`. Panduan ini tidak mengharuskan pembacaan file/env/config credential nyata. Field scopes berlabel comma-separated tetapi loader database melakukan whitespace split/set, bukan parser koma; loader lain tidak menggabungkan scopes pada record. Jangan menjanjikan enforcement scope pada server (`amr_service_client/models/service_credential.py:30`, `amr_service_client/services/credential_loader.py:18`).

Lima tipe resmi: Service Account, Client Secret, API Key, Bearer Token, Basic Auth. API key/bearer/basic membentuk header saja; Basic adalah Base64, bukan enkripsi. Client Secret meminta token client_credentials; Service Account membuat JWT assertion dan meminta token. Generate JSON tidak menerbitkan credential/kunci/token. none/get_jwt hanya cabang factory, bukan pilihan loader/wizard resmi. Referensi: `amr_service_client/wizards/service_credential.py:10`, `amr_service_client/services/auth_factory.py:20`, `amr_service_client/services/providers.py:66`.

Config Credential membuka wizard. Generate JSON menyusun JSON dan data file Base64 dari isian; Save to Credential menulis JSON ke credential context active_id dan mengubah source menjadi database. Pastikan konteks record tepat pada QA berizin; opener memakai default_endpoint_id, tidak membuktikan active_id benar. Simpan/download JSON bukan jaminan aman dan dapat berisi material sensitif. Referensi: `amr_service_client/models/service_credential.py:35`, `amr_service_client/wizards/service_credential.py:48`, `amr_service_client/wizards/service_credential.py:110`, `amr_service_client/wizards/service_credential.xml:62`.

### 3. Service Client

Menu Client mendeklarasikan form name, model_id, each_record, endpoint_id, credential_id, action_next_id, error_handle_id. Tab Iteration Context, Payload, Request, Response, Help berisi konfigurasi kode/ekspresi. Model wajib; each_record menentukan per-record atau seluruh recordset. active tersembunyi pada view dan bukan guard universal eksekusi; active_log tidak ditampilkan pada form client ini. Referensi: `amr_service_client/views/service_client_views.xml:9`, `amr_service_client/views/service_client_views.xml:14`, `amr_service_client/views/service_client_views.xml:26`, `amr_service_client/models/service_client.py:326`.

Hanya penulis kode tepercaya boleh merancang iteration/request/response/payload expression. safe_eval bukan sandbox pengguna tak tepercaya: context memuat env/user/ctx/records. Payload Fixed Value adalah text; Expression dapat mengeksekusi ekspresi/interpolasi; Random Integer mengambil rentang acak. Key ganda ditimpa, error interpolasi bisa menjadi string kosong. Jangan masukkan kode contoh ke sistem live dari panduan ini. Referensi: `amr_service_client/models/service_client.py:362`, `amr_service_client/models/service_client.py:410`, `amr_service_client/models/service_client.py:546`.

### 4. Server action

Extension ir.actions.server menambah jenis/state Service Client dan pilihan service_client_id dengan domain model sama. Source memeriksa client wajib dan model cocok saat state/model_id berubah; dukungan runtime constraint dan _is_recompute belum terbukti. View menyisipkan field dekat link_field_id core; lokasi/rendering aktual perlu QA. Referensi: `amr_service_client/models/actions_server.py:10`, `amr_service_client/models/actions_server.py:21`, `amr_service_client/models/actions_server.py:32`, `amr_service_client/views/ir_actions_views.xml:9`.

Alur action sumber: iteration → payload → request code → HTTP → response handle → next action; each_record mengulang sesuai pilihan. Error di blok HTTP/handle/next dapat diteruskan ke error handler dan tertelan. Error lebih awal tidak otomatis ditangani. HTTP call biasa tidak otomatis raise pada status 4xx/5xx, sehingga next action bukan bukti sukses bisnis. Tidak ada queue/scheduler atau klaim transaksi selesai. Referensi: `amr_service_client/models/service_client.py:198`, `amr_service_client/models/service_client.py:410`.

## Test Connection dan Test Credential

Test Connection membuka wizard dengan method GET/POST/PUT/PATCH/DELETE; path default /api/test/connection/machine, params/headers/payload berbentuk text JSON. Test dapat memicu request nyata bila dijalankan, termasuk metode mutasi: diperlukan izin operasi terpisah. Parse JSON dan resolusi endpoint/client berlangsung sebelum try, sehingga input malformed dapat gagal di luar tampilan handler. success memerlukan HTTP non-error dan response JSON valid; 204 atau non-JSON tidak otomatis dianggap sukses. Referensi: `amr_service_client/models/service_endpoint.py:140`, `amr_service_client/wizards/service_endpoint_test.py:16`, `amr_service_client/wizards/service_endpoint_test.py:29`, `amr_service_client/wizards/service_endpoint_test.xml:10`.

Test Credential api_key/bearer/basic mewarisi UserError Test Credential Not available; itu bukan bukti credential salah di server. Client Secret/Service Account meminta token; notifikasi Credential is valid tidak membuktikan request diterima resource, scope/issuer sah atau isolasi tenant. Provider token dapat menulis token ke debug log, jadi jangan membagikan log/response mentah. Referensi: `amr_service_client/services/providers.py:56`, `amr_service_client/services/providers.py:283`, `amr_service_client/services/providers.py:433`, `amr_service_client/models/service_credential.py:49`.

## Integration Log dan replay

View log menampilkan create_date, endpoint, credential, client dan state; form mempunyai Request Context, Response dan tombol Send. create_date adalah field inherited Odoo, bukan field tambahan lokal. Referensi: `amr_service_client/views/service_client_log_views.xml:9`, `amr_service_client/views/service_client_log_views.xml:24`, `amr_service_client/views/service_client_log_views.xml:42`.

State yang dideklarasikan: outgoing/done/error. done berarti transport HTTP pada jalur log tidak raise, bukan bisnis berhasil, transaksi selesai atau persetujuan server nyata. Direct call tidak otomatis menghasilkan log, dan active_log pada call biasa tidak efektif; jalur dispatch helper/log berbeda. Headers dihapus sebelum persist helper, tetapi URL/params/json/response/error tidak disanitasi penuh. Referensi: `amr_service_client/models/service_client_log.py:18`, `amr_service_client/models/service_client.py:124`, `amr_service_client/models/service_client.py:198`.

Send membaca ulang request_context, membangun auth dan mengirim sinkron, lalu menyimpan state/response. Komentar asynchronous bukan queue/scheduler. Replay belum terbukti berhasil dan tidak idempotent; dapat menggandakan mutasi remote. Jangan menekan Send untuk mengatasi error tanpa otorisasi operasi, penilaian dampak mutasi, dan verifikasi terpisah. Referensi: `amr_service_client/models/service_client_log.py:25`, `amr_service_client/models/service_client_log.py:30`.

## Troubleshooting berbasis sumber

| Gejala | Penjelasan sumber / tindakan aman sebelum QA berizin |
|---|---|
| Menu tidak tampak | Periksa rencana grup teknis dengan administrator; group_no_one berbeda dari ACL. Jangan memberi akses luas untuk memaksa menu terlihat |
| Service not found | Lookup code string hanya active limit=1; tidak ada jaminan code unique. Bandingkan metadata konfigurasi tanpa memanggil layanan |
| Missing/unsupported credential type/source | Loader menerima hanya lima tipe resmi dan tujuh sumber; metadata demo kosong memang bukan credential valid |
| Env/config/parameter/file/JSON error | Nama reference, data atau lokasi dapat hilang/malformed; jangan membaca credential mesin atau mengunggah isinya untuk debugging |
| XML-ID credential gagal | Fallback lookup menimpa variabel string; jangan mengandalkan fallback bekerja |
| Test Credential Not available | Expected base provider static, bukan penolakan auth resource |
| Timeout/non-2xx/non-JSON token | Provider membungkus error; laporan harus tersanitasi dan QA memerlukan izin, bukan mencoba host lain |
| Test endpoint success=false pada 204 | Wizard memanggil response.json; HTTP 204 bukan JSON valid secara otomatis |
| URL tidak sesuai prefix | Slash awal path melewati base_path; None/False berbeda dari path kosong |
| Log tidak muncul | Direct call berbeda dari dispatch/log; active_log bukan jaminan semua call tercatat |
| Error action terlihat hilang | error_handle_id bisa menelan exception; HTTP 4xx/5xx direct call tidak otomatis raise |
| Token lama/antar konteks tidak sesuai | Cache module-global dan key tidak lengkap; rotasi/scope/DB perlu QA dan keputusan reviewer |

Referensi diagnosis: `amr_service_client/models/service_client.py:462`, `amr_service_client/services/credential_loader.py:112`, `amr_service_client/services/providers.py:230`, `amr_service_client/services/token_cache.py:13`, serta bagian alur/wizard di atas. Diagnosis ini belum membuktikan hasil runtime tertentu.

## FAQ

- Apakah addon menyediakan login OIDC interaktif? Tidak ada flow discovery/PKCE/refresh-token/ID-token validation pada provider yang dijelaskan; ini client bridge, bukan IdP (`amr_service_client/services/providers.py:203`, `amr_service_client/services/providers.py:312`).
- Apakah menu tersembunyi melindungi credential? Tidak dapat diklaim; internal user punya read ACL persistent dan isolasi company/field belum dibuktikan (`amr_service_client/security/ir.model.access.csv:2`).
- Apakah active=false memblokir seluruh request? Tidak ada guard universal; gunakan batas tidak auto-load/tidak mengeksekusi, bukan mengandalkan active (`amr_service_client/models/service_client.py:410`).
- Apakah done berarti transaksi bisnis sukses? Tidak, hanya status transport pada jalur log (`amr_service_client/models/service_client_log.py:37`).
- Apakah replay aman diulang? Belum terbukti, tidak ada idempotency dan dapat memutasi remote berulang (`amr_service_client/models/service_client_log.py:30`).
- Apakah Generate membuat credential sah? Tidak, hanya serialisasi isian JSON (`amr_service_client/wizards/service_credential.py:48`).
- Apakah endpoint demo boleh dites? Tidak. https://resource.example.invalid adalah metadata sintetis; jangan DNS/HTTP ke domain itu. JSON hanya tiga objek alias, tanpa ID DB/material credential, Service Client nonaktif/log off, tanpa kode; bukan data ORM installable.
- Apakah dokumentasi menyatakan aman/kompatibel? Tidak. Kerahasiaan credential, isolasi company, trust outbound/server, logging data sensitif, cache/expiry, kontrak API, lookup/error/replay, payload/wizard/scopes dan kompatibilitas Odoo 13 tetap memiliki batas teknis yang dijelaskan di atas. UI/ACL/registry/runtime **belum diverifikasi pada runtime Odoo 13**.

## Batas verifikasi

Panduan ini hanya berdasarkan sumber. Pemeriksaan dokumen, tautan, sitasi dan metadata JSON tidak membuktikan instalasi, keamanan, penerimaan server, atau kompatibilitas Odoo/DB/layanan. Verifikasi runtime pada lingkungan yang diotorisasi diperlukan sebelum penggunaan nyata; jangan menganggap panduan sebagai izin install/deploy/publish.

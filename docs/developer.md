# Panduan Developer — amr_service_client

## Ruang lingkup dan provenance sumber

Dokumen ini menjelaskan deklarasi sumber, bukan hasil pengujian. Semua perilaku ORM, registry, ACL, UI, wizard dan integrasi **belum diverifikasi pada runtime Odoo 13**. Penggunaan dibatasi untuk development/demo, bukan produksi; dokumentasi tidak membuktikan keamanan atau kompatibilitas runtime.

Pin sumber upstream: `7a6f09bef97f38d53566b1351c3178c536fdb4e4`.

Lihat [panduan user](user.md) dan [metadata demo](examples/service-client-demo.json). Batas teknis yang perlu diperhatikan meliputi kemungkinan pembacaan credential, outbound/remote mutation, eksekusi action, serta replay berulang; dokumentasi tidak memperbaikinya.

## Fungsi addon dan manifest

Addon ini client HTTP/JSON-RPC Odoo 13 ke amr_resource, bukan IdP, bukan resource server, bukan validator ID-token. Manifest mendeklarasikan nama Service Client, kategori Tools, versi 13.0.0.1.0, LGPL-3; depends base, web, base_setup, amr_resource; external_dependencies python berisi pyjwt. Ejaan dependency tersebut adalah deklarasi manifest, bukan bukti paket berhasil tersedia. Sumber juga mengimpor requests dan jwt; dukungan backend kriptografi/library belum dibuktikan. Referensi: `amr_service_client/__manifest__.py:2`, `amr_service_client/__manifest__.py:6`, `amr_service_client/__manifest__.py:9`, `amr_service_client/services/providers.py:3`.

Data manifest: ACL CSV, view server action, endpoint, credential, client, log, menu, serta dua view wizard. Tidak ada demo, scheduler, cron, hook atau fixture JSON dokumentasi dalam manifest. Lihat `amr_service_client/__manifest__.py:12`. amr_resource adalah dependency Resource Server terpisah.

## Import graph dan batas API aktif

Root mengimpor models → services → wizards (`amr_service_client/__init__.py:3`). Models mengimpor service_credential, service_endpoint, service_client, service_client_log, actions_server (`amr_service_client/models/__init__.py:3`). Services mengimpor credential_loader, auth_factory, providers, token_cache; auth_factory mengimpor kelas providers (`amr_service_client/services/__init__.py:3`, `amr_service_client/services/auth_factory.py:5`). Wizards mengimpor service_credential lalu service_endpoint_test (`amr_service_client/wizards/__init__.py:3`). Ini reachability statis, bukan urutan registry yang telah diuji.

`services/service_client.py` adalah duplikat historis yang **tidak diimpor** (baris import dikomentari: `amr_service_client/services/__init__.py:4`). Ia mendeklarasikan service.client sebagai AbstractModel, sedangkan file models aktif mendeklarasikan Model. Jangan aktifkan atau mengiklankan duplikat sebagai API aktif. Inventaris di bawah memisahkannya dari API aktif.

## Endpoint dan kontrak URL

Sumber URL: value memakai base_url_value; env membaca nama environment pada config_param_name; config membaca key konfigurasi Odoo; config_parameter membaca ir.config_parameter dengan sudo. open_config_parameter dapat mencari/membuat parameter dan mengembalikan action form; ini bukan operasi baca murni. Referensi: `amr_service_client/models/service_endpoint.py:44`, `amr_service_client/models/service_endpoint.py:63`.

get_url(path=None): None/False mengembalikan url hasil compute; string kosong atau '/' mengembalikan host base. Path relatif tanpa slash awal memperoleh base_path jika ada; path yang diawali '/' melewati base_path dan ditempelkan ke host. Istilah absolute di sini berarti path berawalan '/', bukan dukungan URL absolut penuh sebagai override host. Source tidak melakukan validasi HTTPS atau allowlist host. Compute mengakses self.base_path di dalam loop rec, sehingga multi-record perlu QA. code indexed dan required tetapi tidak memiliki deklarasi unique meskipun Help view menyebut unique. Referensi: `amr_service_client/models/service_endpoint.py:81`, `amr_service_client/models/service_endpoint.py:105`, `amr_service_client/models/service_endpoint.py:168`, `amr_service_client/views/service_endpoint_views.xml:81`.

Timeout endpoint default 30 detik. Header default Content-Type=text/plain dan Accept=application/json, meskipun transport mengirim argumen json. Header caller dipertahankan dengan setdefault lalu auth provider dapat menimpa Authorization/header tertentu. Referensi: `amr_service_client/models/service_endpoint.py:29`, `amr_service_client/models/service_endpoint.py:128`, `amr_service_client/models/service_client.py:181`.

## Credential: tujuh sumber dan batas validasi

| source | Data yang dibaca menurut sumber | Batas/error |
|---|---|---|
| database | credential_json melalui json.loads | Hanya loader ini merge scope/scopes dan field scopes melalui whitespace split dan set; bukan parser koma; urutan bisa berubah |
| file_path | reference sebagai lokasi file JSON | open/json dapat gagal; bukan lokasi tervalidasi/allowlist |
| env_json | reference sebagai nama env berisi JSON | Kosong/hilang: ValueError; JSON malformed tetap error |
| env_path | reference sebagai nama env berisi lokasi file JSON | ValueError bila env hilang; error file/JSON diteruskan |
| config_path | reference sebagai key config Odoo berisi lokasi file | ValueError bila kosong; file/JSON error diteruskan |
| system_parameter_json | reference sebagai key parameter sudo berisi JSON | ValueError bila kosong; JSON error diteruskan |
| system_parameter_path | parameter sudo berisi lokasi file JSON | ValueError bila kosong; file/JSON error diteruskan |

Referensi masing-masing loader: `amr_service_client/services/credential_loader.py:12`, `amr_service_client/services/credential_loader.py:27`, `amr_service_client/services/credential_loader.py:36`, `amr_service_client/services/credential_loader.py:48`, `amr_service_client/services/credential_loader.py:61`, `amr_service_client/services/credential_loader.py:74`, `amr_service_client/services/credential_loader.py:86`.

Validator hanya memeriksa keberadaan type dan membership lima tipe service_account, client_secret, api_key, bearer, basic. Ia bukan validasi lengkap schema/object, material, issuer atau autentikasi remote. Missing type/unsupported type/source menghasilkan ValueError; struktur non-object bisa gagal dengan exception Python lain. Lookup string mencari name limit=1; fallback env.ref memakai variabel yang telah ditimpa recordset, sehingga XML-ID fallback tidak dapat dijanjikan bekerja. load_cached didekorasi ormcache credential.id/write_date, tetapi get_credential_provider memanggil load_credential biasa; rotasi file/env tidak otomatis menjadi write_date. Referensi: `amr_service_client/services/credential_loader.py:99`, `amr_service_client/services/credential_loader.py:112`, `amr_service_client/services/credential_loader.py:121`, `amr_service_client/services/credential_loader.py:141`.

## Auth provider, token dan cache

| Tipe | Perilaku statis | Batas |
|---|---|---|
| api_key | Header dinamis dari header/value | Tidak membuktikan server menerima credential |
| bearer | Authorization Bearer dari token statis | Tidak memvalidasi signature/issuer/expiry |
| basic | Authorization Basic dari Base64 username/password | Base64 bukan enkripsi |
| client_secret | POST form client_credentials dengan client_id/client_secret; audience dan scope opsional | Bukan interactive login, discovery, PKCE, refresh-token atau ID-token validation |
| service_account | POST JWT bearer assertion; penandatanganan JWT | Trust server, kunci, scope dan penerimaan resource belum teruji |

Referensi: `amr_service_client/services/providers.py:66`, `amr_service_client/services/providers.py:76`, `amr_service_client/services/providers.py:86`, `amr_service_client/services/providers.py:203`, `amr_service_client/services/providers.py:312`.

Factory juga memiliki cabang none/get_jwt dan credential kosong → NoneAuthProvider, tetapi loader/wizard resmi hanya lima tipe tadi. Bukan opsi no-auth/get_jwt yang didukung UI. Base test_credential (termasuk api_key/bearer/basic) melempar UserError Test Credential Not available. None test tidak melakukan apa pun. Test client_secret/service_account meminta token; notifikasi sukses pada model bukan bukti resource menerima request. get_jwt mengharapkan cache_ttl di _get_token tetapi _request_token tidak mengembalikannya. Referensi: `amr_service_client/services/auth_factory.py:20`, `amr_service_client/services/providers.py:56`, `amr_service_client/services/providers.py:104`, `amr_service_client/services/providers.py:165`, `amr_service_client/models/service_credential.py:49`.

Provider token memakai connect/read timeout default 10/30; Timeout/ConnectionError dibungkus ValueError, non-2xx menjadi ValueError dengan data error remote, respons bukan JSON menjadi Invalid token response, access_token wajib. expires_in dikonversi int, default 3600; cache_ttl=max(expires_in-60,60), sehingga minimum 60 bisa melampaui token berumur pendek. Header resource tetap Bearer tanpa mengikuti token_type respons. Referensi: `amr_service_client/services/providers.py:230`, `amr_service_client/services/providers.py:259`, `amr_service_client/services/providers.py:346`, `amr_service_client/services/providers.py:375`.

Assertion service_account: iss=sub=client_id, aud=token_uri, iat saat ini, exp=iat+300, jti UUID; audience opsional menjadi resource, scope string/list menjadi claim. Kunci dari private_key atau private_key_file; tidak ada proteksi lokasi file di sini. Algoritme default RS256; whitelist RS256/384/512 dan ES256/384/512. kid opsional di client (private_key_id atau kid); kontrak pasangan server yang mensyaratkan kid masih perlu pengujian terpisah dan bukan jaminan interoperabilitas. Referensi client: `amr_service_client/services/providers.py:21`, `amr_service_client/services/providers.py:292`, `amr_service_client/services/providers.py:392`.

TOKEN_CACHE adalah dictionary module-global per proses; get menghapus entry expired, set menggunakan datetime.now dan tools.timedelta. Tidak ada namespace DB/company; key client_secret memasukkan client_id/audience/token_uri tetapi tidak scope/material rotasi; service_account juga tidak memasukkan token_uri. Tidak ada jaminan koherensi multi-worker atau isolasi tenant. is_token_expired melakukan decode tanpa signature/exp verification lalu membandingkan exp; itu bukan validasi token (tanpa exp dianggap belum expired). Referensi: `amr_service_client/services/token_cache.py:13`, `amr_service_client/services/token_cache.py:20`, `amr_service_client/services/providers.py:38`, `amr_service_client/services/providers.py:185`, `amr_service_client/services/providers.py:309`.

## Client HTTP, proxy dan return/error

Factory ORM menerima code string aktif (search limit=1), integer browse, atau record endpoint; missing endpoint ValueError. Pemilihan credential: explicit, lalu endpoint, lalu credential client pada record factory bila relevan. Tidak ada unique code atau guard active universal untuk record/integer. Konstruktor menyimpan credential hasil resolusi tetapi load memakai argumen awal, sehingga fallback perlu negative test. Referensi: `amr_service_client/models/service_client.py:161`, `amr_service_client/models/service_client.py:462`.

ServiceClient.call mengembalikan requests.Response tanpa raise_for_status; exception transport diteruskan. Parameter audience pada call tidak diteruskan ke prepare_request_context; active_log pada call tidak dipakai. Sumber memilih method per-call terlebih dahulu, baru constructor method (bukan constructor selalu override). path memakai path or self.path sehingga string kosong dapat berubah menjadi fallback. prepare_request_context sendiri menerima audience. Context manager hanya return self/no-op exit, bukan transaksi/koneksi lifecycle. Referensi: `amr_service_client/models/service_client.py:174`, `amr_service_client/models/service_client.py:181`, `amr_service_client/models/service_client.py:198`.

normalize_json mempertahankan primitive/None; date/datetime melalui formatter Odoo; bytes/bytearray Base64, UUID str, Decimal float (risiko presisi), dict rekursif, list/tuple/set menjadi list (set tidak menjamin urutan), objek lain str. Ini bukan validasi payload bisnis. Referensi: `amr_service_client/models/service_client.py:62`.

RemoteObjectProxy POST /api/dataset/call_kw, JSON-RPC 2.0 method call id=1, model/method/args/kwargs/context. raise_for_status pada HTTP dan RuntimeError jika envelope memiliki error; JSON decoding error diteruskan. result falsy (0/False/None) menjadi []; bukan pelestarian return asli. search_read memakai fallback or sehingga offset=0/limit=0/domain kosong bisa memakai default tersimpan. external_data_callback membaca halaman lalu memanggil callback sinkron per item dengan offset/total; callback error diteruskan. Bukan queue, scheduler atau bukti commit transaksi remote. Referensi: `amr_service_client/models/service_client.py:246`, `amr_service_client/models/service_client.py:275`, `amr_service_client/models/service_client.py:297`.

## Action, payload, logging dan replay

Server action menambah state service_client dan relasi ke client ber-model sama; constraint dipicu state/model_id (tidak menyebut service_client_id). run_action_service_client_multi memakai _is_recompute(action), kompatibilitas core belum teruji. Referensi: `amr_service_client/models/actions_server.py:10`, `amr_service_client/models/actions_server.py:21`, `amr_service_client/models/actions_server.py:32`.

Alur: each_record menentukan per-record atau recordset; iteration mengeksekusi kode untuk daftar konteks response; context di-update, payload disusun, code request dievaluasi, HTTP dipanggil, handle response, kemudian action_next_id. Error dalam blok HTTP/handle/next dapat dialihkan ke error_handle_id dan tertelan; error iteration/payload/code/konstruksi client berada sebelum try tersebut. run_action mengembalikan action terakhir atau None; send_request tidak return hasilnya. Tidak ada guard active universal. safe_eval mendapatkan env/user/ctx dan konteks records terkait; bukan sandbox aman untuk penulis tak tepercaya. Pemeriksaan sintaks test_python_expr bukan validasi keamanan. Referensi: `amr_service_client/models/service_client.py:362`, `amr_service_client/models/service_client.py:371`, `amr_service_client/models/service_client.py:404`, `amr_service_client/models/service_client.py:410`.

Payload fix mempertahankan text; exp memakai safe_eval atau interpolasi ${...}; custom_render mengganti ekspresi error menjadi string kosong dengan logging; random_int memilih 0 sampai batas digit atau default 1000. None/non-string/negatif dan duplicate key memerlukan test; duplicate key ditimpa entri terakhir. get_type_display memakai label record meskipun selection exp, sehingga label exp tidak sesuai. Referensi: `amr_service_client/models/service_client.py:518`, `amr_service_client/models/service_client.py:530`, `amr_service_client/models/service_client.py:534`, `amr_service_client/models/service_client.py:546`.

Direct call tidak membuat log otomatis. Jalur ServiceClientSend.dispatch_send berbeda: request, raise_for_status, lalu jika aktif/error membuat service.client.log sudo; return log atau None. prepare_payload membentuk helper, bukan menjadwalkan. Ada risiko atribut endpoint_id pada helper/client dan response None pada penanganan exception (logging response.text dapat menutupi error asli). Header dibuang sebelum persist, tetapi URL/params/json/response, traceback dan pesan error tidak disanitasi penuh. Provider Test Credential menulis objek respons token ke debug log; jangan aktifkan/log/share output mentah sebagai bukti aman. Referensi: `amr_service_client/models/service_client.py:104`, `amr_service_client/models/service_client.py:124`, `amr_service_client/models/service_client.py:215`, `amr_service_client/services/providers.py:283`, `amr_service_client/services/providers.py:433`.

Log.dispatch_send memanggil send sinkron meskipun komentar menyebut asynchronous. Replay parsing request_context, membangun auth baru lalu mengirim ulang dan menulis state/response; return self. done hanya status transport setelah HTTP tidak error, bukan sukses bisnis/transaksi. Tidak ada idempotency, retry policy, queue/cron atau jaminan replay berhasil; replay dapat mengulang mutasi remote. Referensi: `amr_service_client/models/service_client_log.py:18`, `amr_service_client/models/service_client_log.py:25`, `amr_service_client/models/service_client_log.py:30`.

## Wizard dan UI teknis

Credential wizard Generate membentuk JSON/file Base64 dari isian, bukan menerbitkan credential, kunci atau token. Save to Credential memakai active_id dan mengganti source ke database; action_save hanya menulis JSON. Konteks opener default_endpoint_id tidak menjamin active_id benar. Endpoint test wizard menyimpan endpoint_id sebagai Integer dan endpoint_model sebagai Char, parse params/headers/payload serta resolusi client sebelum try; error tahap itu tidak ditangkap oleh handler test. Success membutuhkan HTTP non-error dan response.json berhasil; 204/bukan JSON tidak otomatis sukses. Referensi: `amr_service_client/wizards/service_credential.py:48`, `amr_service_client/wizards/service_credential.py:103`, `amr_service_client/wizards/service_credential.py:110`, `amr_service_client/models/service_credential.py:35`, `amr_service_client/wizards/service_endpoint_test.py:29`.

Menu Integration di parent base.menu_users dengan submenu Endpoints, Credentials, Client, Integration Log dibatasi base.group_no_one. Itu deklarasi visibility, bukan otorisasi ORM/RPC. Persistent credential/endpoint/client/log/payload: internal user base.group_user read; base.group_erp_manager CRUD. Kedua wizard memberi CRUD kepada base.group_user. Tidak ada deklarasi company_id, record-rule company atau pembatasan groups field secret dalam addon ini; tidak ada bukti tenant/company/field isolation, termasuk karena sudo pada parameter/log. Efek inherited/core/dependency tetap belum diverifikasi. Referensi: `amr_service_client/views/menuitem.xml:3`, `amr_service_client/security/ir.model.access.csv:2`, `amr_service_client/security/ir.model.access.csv:17`.

## Kompatibilitas dan batas operasional

Deklarasi versi 13.0 tidak membuktikan instalasi. tools.timedelta, _is_recompute, signature server action, xpath link_field_id, XML IDs/group/menu, ORM multi-record, pyjwt/jwt/crypto dan versi Python/core memerlukan verifikasi pada lingkungan QA yang diotorisasi. Referensi: `amr_service_client/services/token_cache.py:29`, `amr_service_client/models/actions_server.py:32`, `amr_service_client/views/ir_actions_views.xml:9`.

Pembacaan sumber dan pemeriksaan dokumentasi tidak membuktikan registry/UI/ACL/company isolation maupun autentikasi layanan berpasangan. Pengujian offline dengan mock tidak membuktikan kriptografi, trust server, atau interoperabilitas runtime. Operasi Odoo/DB/layanan dan pengujian integrasi memerlukan lingkungan serta izin tersendiri; panduan ini tidak memberi izin operasi tersebut.

Metadata demo hanya untuk dibaca: synthetic=true, auto_load=false, live_call=false; tepat tiga objek dengan alias, credential kosong, Service Client inactive/log off, tanpa kode executable. Tidak installable ORM data, tidak boleh dimuat manifest/init/hook/cron, dan domain example.invalid tidak boleh dihubungi. active=false saja bukan kontrol keselamatan; tidak dimuat/tidak dieksekusi adalah batas fixture.

Rollout/rollback memerlukan otorisasi lingkungan serta rencana backup/schema. Git rollback tidak membatalkan side effect remote.

## Inventaris deklarasi model dan field lokal

Inventaris berikut dibaca statis dengan AST tanpa import/exec. Satu baris field adalah satu deklarasi lokal, bukan seluruh field registry. Field otomatis Odoo (id/create_uid/create_date/write_uid/write_date dan lainnya) serta field dari dependency/core tidak diinventaris sebagai field lokal. `service.endpoint` mewarisi field mixin secara terpisah; `ir.actions.server` mempertahankan field core dan hanya memperluas state/menambah service_client_id. Model abstract loader/factory/cache tidak mendeklarasikan field. Duplikat unloaded dipisah.

### ServerActions: (extension)

Jenis `models.Model`; _name=tidak dideklarasikan; _inherit=ir.actions.server; reachable secara statis. Sumber: `amr_service_client/models/actions_server.py:7`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| state | Selection | selection_add=[('service_client', 'Service Client')] | `amr_service_client/models/actions_server.py:10` |
| service_client_id | Many2one | 'service.client'; 'Service Client'; domain="[('model_id', '=', model_id)]"; help='Service Client to use for Http Request or RCP.' | `amr_service_client/models/actions_server.py:14–18` |

### ServiceClientFactory: service.client

Jenis `models.Model`; _name=service.client; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/models/service_client.py:322`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| active | Boolean | default=True; help='When unchecked, the rule is hidden and will not be executed.' | `amr_service_client/models/service_client.py:326` |
| name | Char | Tanpa argumen tambahan | `amr_service_client/models/service_client.py:327` |
| model_id | Many2one | 'ir.model'; string='Model'; required=True; ondelete='cascade' | `amr_service_client/models/service_client.py:328` |
| endpoint_id | Many2one | 'service.endpoint' | `amr_service_client/models/service_client.py:329` |
| credential_id | Many2one | 'service.credential' | `amr_service_client/models/service_client.py:330` |
| active_log | Boolean | Tanpa argumen tambahan | `amr_service_client/models/service_client.py:331` |
| each_record | Boolean | string='Each Record'; default=False; help='If checked, the action will be executed for each record in the recordset.' | `amr_service_client/models/service_client.py:332` |
| iteration | Text | 'Iteration Context'; default=DEFAULT_INTERATION_CONTEXT_CODE; help="Expression returning the interation contextThis context will be available in the python code asctx.get('iteration')." | `amr_service_client/models/service_client.py:337` |
| code | Text | string='Python Code'; default=DEFAULT_PYTHON_CODE; help='Write Python code that the action will execute. Some variables are available for use; help about python expression is given in the help tab.' | `amr_service_client/models/service_client.py:345` |
| handle | Text | string='Python Code Handle'; default=DEFAULT_PYTHON_CODE_HANDLE; help='Write Python code handle response that the action will execute. Some variables are available for use; help about python expression is given in the help tab.' | `amr_service_client/models/service_client.py:352` |
| action_next_id | Many2one | 'ir.actions.server' | `amr_service_client/models/service_client.py:358` |
| payload_ids | One2many | 'service.client.payload'; 'service_client_id' | `amr_service_client/models/service_client.py:359` |
| error_handle_id | Many2one | 'ir.actions.server' | `amr_service_client/models/service_client.py:360` |

### ServiceClientPayload: service.client.payload

Jenis `models.Model`; _name=service.client.payload; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/models/service_client.py:518`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| key | Char | 'Key' | `amr_service_client/models/service_client.py:521` |
| value | Text | 'Value' | `amr_service_client/models/service_client.py:522` |
| type | Selection | [('fix', 'Fixed Value'), ('exp', 'Expression'), ('random_int', 'Random Integer')]; 'Type'; default='fix' | `amr_service_client/models/service_client.py:523` |
| service_client_id | Many2one | 'service.client' | `amr_service_client/models/service_client.py:528` |

### ServiceClientLog: service.client.log

Jenis `models.Model`; _name=service.client.log; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/models/service_client_log.py:13`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| state | Selection | [('outgoing', 'Outgoing'), ('done', 'Done'), ('error', 'Error')] | `amr_service_client/models/service_client_log.py:18` |
| endpoint_id | Many2one | 'service.endpoint' | `amr_service_client/models/service_client_log.py:19` |
| credential_id | Many2one | 'service.credential' | `amr_service_client/models/service_client_log.py:20` |
| client_id | Many2one | 'service.client' | `amr_service_client/models/service_client_log.py:21` |
| request_context | Text | Tanpa argumen tambahan | `amr_service_client/models/service_client_log.py:22` |
| response | Text | Tanpa argumen tambahan | `amr_service_client/models/service_client_log.py:23` |

### ServiceCredential: service.credential

Jenis `models.Model`; _name=service.credential; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/models/service_credential.py:11`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| name | Char | required=True | `amr_service_client/models/service_credential.py:15` |
| source | Selection | [('database', 'Database'), ('file_path', 'File Path'), ('env_json', 'Environment JSON'), ('env_path', 'Environment Path'), ('config_path', 'Config Path'), ('system_parameter_json', 'System Parameter JSON'), ('system_parameter_path', 'System Parameter Path')]; required=True | `amr_service_client/models/service_credential.py:16` |
| reference | Char | Tanpa argumen tambahan | `amr_service_client/models/service_credential.py:28` |
| credential_json | Text | Tanpa argumen tambahan | `amr_service_client/models/service_credential.py:29` |
| scopes | Char | help='Comma-separated scopes' | `amr_service_client/models/service_credential.py:30` |

### ServiceEndpointMixin: service.endpoint.mixin

Jenis `models.AbstractModel`; _name=service.endpoint.mixin; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/models/service_endpoint.py:14`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| base_url | Char | compute='_compute_base_url' | `amr_service_client/models/service_endpoint.py:17` |
| url | Char | compute='_compute_base_url' | `amr_service_client/models/service_endpoint.py:18` |
| base_url_value | Char | Tanpa argumen tambahan | `amr_service_client/models/service_endpoint.py:19` |
| source | Selection | [('value', 'Value'), ('env', 'OS Environment'), ('config', 'Odoo Config'), ('config_parameter', 'System Parameter')]; required=True; default='value' | `amr_service_client/models/service_endpoint.py:20` |
| content_type_default | Selection | [('text/plain', 'text/plain'), ('application/json', 'application/json')]; required=True; default='text/plain' | `amr_service_client/models/service_endpoint.py:29` |
| config_param_name | Char | Tanpa argumen tambahan | `amr_service_client/models/service_endpoint.py:36` |
| base_path | Char | help='/api/v1' | `amr_service_client/models/service_endpoint.py:37` |
| audience | Char | Tanpa argumen tambahan | `amr_service_client/models/service_endpoint.py:38` |
| credential_id | Many2one | 'service.credential' | `amr_service_client/models/service_endpoint.py:39` |
| timeout | Integer | default=30 | `amr_service_client/models/service_endpoint.py:40` |
| active | Boolean | default=True | `amr_service_client/models/service_endpoint.py:41` |
| active_log | Boolean | Tanpa argumen tambahan | `amr_service_client/models/service_endpoint.py:42` |

### ServiceEndpoint: service.endpoint

Jenis `models.Model`; _name=service.endpoint; _inherit=service.endpoint.mixin; reachable secara statis. Sumber: `amr_service_client/models/service_endpoint.py:164`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| name | Char | required=True | `amr_service_client/models/service_endpoint.py:168` |
| code | Char | required=True; index=True | `amr_service_client/models/service_endpoint.py:169` |

### ServiceAuthFactory: service.auth.factory

Jenis `models.AbstractModel`; _name=service.auth.factory; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/auth_factory.py:16`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialLoaderDatabase: service.credential.loader.database

Jenis `models.AbstractModel`; _name=service.credential.loader.database; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/credential_loader.py:12`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialLoaderFilePath: service.credential.loader.file_path

Jenis `models.AbstractModel`; _name=service.credential.loader.file_path; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/credential_loader.py:27`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialLoaderEnvJson: service.credential.loader.env_json

Jenis `models.AbstractModel`; _name=service.credential.loader.env_json; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/credential_loader.py:36`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialLoaderEnvPath: service.credential.loader.env_path

Jenis `models.AbstractModel`; _name=service.credential.loader.env_path; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/credential_loader.py:48`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialLoaderConfigPath: service.credential.loader.config_path

Jenis `models.AbstractModel`; _name=service.credential.loader.config_path; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/credential_loader.py:61`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialLoaderParameterJson: service.credential.loader.system_parameter_json

Jenis `models.AbstractModel`; _name=service.credential.loader.system_parameter_json; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/credential_loader.py:74`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialLoaderParameterPath: service.credential.loader.system_parameter_path

Jenis `models.AbstractModel`; _name=service.credential.loader.system_parameter_path; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/credential_loader.py:86`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialLoader: service.credential.loader

Jenis `models.AbstractModel`; _name=service.credential.loader; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/credential_loader.py:108`.

Tidak ada field lokal yang dideklarasikan.

### ServiceClientFactory: service.client

Jenis `models.AbstractModel`; _name=service.client; _inherit=tidak dideklarasikan; UNLOADED — tidak masuk import graph. Sumber: `amr_service_client/services/service_client.py:215`.

Tidak ada field lokal yang dideklarasikan.

### ServiceTokenCache: service.token.cache

Jenis `models.AbstractModel`; _name=service.token.cache; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/services/token_cache.py:16`.

Tidak ada field lokal yang dideklarasikan.

### ServiceCredentialWizard: service.credential.wizard

Jenis `models.TransientModel`; _name=service.credential.wizard; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/wizards/service_credential.py:6`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| credential_type | Selection | [('service_account', 'Service Account'), ('client_secret', 'Client Secret'), ('api_key', 'API Key'), ('bearer', 'Bearer Token'), ('basic', 'Basic Auth')]; required=True; default='service_account' | `amr_service_client/wizards/service_credential.py:10` |
| version | Char | default='1.0' | `amr_service_client/wizards/service_credential.py:21` |
| json_content | Text | readonly=True | `amr_service_client/wizards/service_credential.py:23` |
| generated_file | Binary | readonly=True | `amr_service_client/wizards/service_credential.py:24` |
| generated_filename | Char | readonly=True | `amr_service_client/wizards/service_credential.py:25` |
| client_id | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:28` |
| private_key_id | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:29` |
| private_key | Text | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:30` |
| private_key_file | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:31` |
| token_uri | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:32` |
| client_secret | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:33` |
| header | Char | default='X-API-Key' | `amr_service_client/wizards/service_credential.py:34` |
| value | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:35` |
| token | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:38` |
| username | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:41` |
| password | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_credential.py:42` |

### ServiceEndpointTestWizard: service.endpoint.test.wizard

Jenis `models.TransientModel`; _name=service.endpoint.test.wizard; _inherit=tidak dideklarasikan; reachable secara statis. Sumber: `amr_service_client/wizards/service_endpoint_test.py:10`.

| Field lokal | Tipe | Relasi/selection/default/atribut deklaratif | Sumber |
|---|---|---|---|
| endpoint_id | Integer | Tanpa argumen tambahan | `amr_service_client/wizards/service_endpoint_test.py:14` |
| endpoint_model | Char | Tanpa argumen tambahan | `amr_service_client/wizards/service_endpoint_test.py:15` |
| method | Selection | [('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('PATCH', 'PATCH'), ('DELETE', 'DELETE')]; required=True; default='GET' | `amr_service_client/wizards/service_endpoint_test.py:16` |
| path | Char | required=True; default='/api/test/connection/machine' | `amr_service_client/wizards/service_endpoint_test.py:20` |
| params | Text | Tanpa argumen tambahan | `amr_service_client/wizards/service_endpoint_test.py:21` |
| headers | Text | Tanpa argumen tambahan | `amr_service_client/wizards/service_endpoint_test.py:22` |
| payload | Text | Tanpa argumen tambahan | `amr_service_client/wizards/service_endpoint_test.py:23` |
| response_status | Integer | readonly=True | `amr_service_client/wizards/service_endpoint_test.py:25` |
| response_body | Text | readonly=True | `amr_service_client/wizards/service_endpoint_test.py:26` |
| success | Boolean | readonly=True | `amr_service_client/wizards/service_endpoint_test.py:27` |

## Konstruktor dan protokol helper Python

| Helper aktif | Signature deklaratif | Return/batas |
|---|---|---|
| AuthenticationProvider | `__init__(self, env, credential)` | Inisialisasi env/credential, None; subclass mewarisi kecuali override. `amr_service_client/services/providers.py:33` |
| ServiceClient | `__init__(self, env, endpoint, credential, path=None, method=None, client_id=None)` | Inisialisasi provider; error resolver/loader/factory diteruskan. `amr_service_client/models/service_client.py:161` |
| ServiceClientSend | `__init__(self, service_client, payload, active_log=False, endpoint_id=None, credential_id=None)` | Normalisasi payload dan simpan referensi, None; attribute/type errors dapat diteruskan. `amr_service_client/models/service_client.py:106` |
| RemoteObjectProxy | `__init__(self, client, model_name, **kwargs)` | Simpan context/domain/fields/offset/limit/order, None. `amr_service_client/models/service_client.py:223` |
| Client dan proxy | `__enter__(self)`, `__exit__(self, *args)` | Enter return self; exit None, tidak menelan exception atau menutup transaksi. `amr_service_client/models/service_client.py:174`, `amr_service_client/models/service_client.py:233` |
| Proxy | `__getattr__(self, method_name)` | Return callable `method(*args, **kwargs)` yang mengirim proxy call. `amr_service_client/models/service_client.py:240` |
| Proxy | `__str__(self)`, alias `__repr__` | String remote.RemoteModel(model_name). `amr_service_client/models/service_client.py:316` |
| Duplikat UNLOADED | `ServiceClient.__init__(self, env, endpoint, credential)` | Tidak aktif, tidak memiliki path/method/client_id constructor aktif. `amr_service_client/services/service_client.py:62` |

## Katalog signature metode publik

Katalog mencakup setiap metode publik lokal (termasuk helper Python dan duplikat unloaded), bukan API registry teruji. Argumen self tetap ditampilkan. Error ORM/ensure_one/akses dan boundary file/JSON/HTTP dapat diteruskan selain error eksplisit pada uraian. Metode private penting dijelaskan pada bagian kontrak; dunder context manager return self/no-op exit, proxy __getattr__ menghasilkan callable, __str__/__repr__ menghasilkan label remote.RemoteModel.

| Kelas.metode dan signature | Return/error menurut sumber | Sumber |
|---|---|---|
| `ServerActions.run_action_service_client_multi(self, action, eval_context=None)` | False bila client hilang/recompute; selain itu hasil action client. _is_recompute belum teruji. | `amr_service_client/models/actions_server.py:32` |
| `normalize_json(value)` | Nilai JSON-compatible rekursif; formatter/coercion error dapat diteruskan. | `amr_service_client/models/service_client.py:62` |
| `ServiceClientSend.dispatch_send(self)` | Helper: log record jika logging/error atau None; log model: self setelah send sinkron. Penanganan error dapat menutupi error awal. | `amr_service_client/models/service_client.py:124` |
| `ServiceClient.prepare_request_context(self, path=None, method=None, params=None, payload=None, headers=None, audience=None)` | Dict kwargs requests berisi auth; error resolver/provider diteruskan. | `amr_service_client/models/service_client.py:181` |
| `ServiceClient.call(self, method=None, path=None, params=None, payload=None, headers=None, audience=None, active_log=False)` | HTTP client/ORM: Response tanpa raise_for_status; proxy: result atau [] dan raise HTTPError/RuntimeError/JSON error. audience call HTTP tidak diteruskan. | `amr_service_client/models/service_client.py:198` |
| `ServiceClient.get(self, path=None, params=None, **kwargs)` | Response melalui call GET; exception transport/provider diteruskan. | `amr_service_client/models/service_client.py:203` |
| `ServiceClient.post(self, path=None, payload=None, **kwargs)` | Response melalui call POST; exception transport/provider diteruskan. | `amr_service_client/models/service_client.py:206` |
| `ServiceClient.put(self, path=None, payload=None, **kwargs)` | Response melalui call PUT; exception transport/provider diteruskan. | `amr_service_client/models/service_client.py:209` |
| `ServiceClient.delete(self, path=None, **kwargs)` | Response melalui call DELETE; exception transport/provider diteruskan. | `amr_service_client/models/service_client.py:212` |
| `ServiceClient.prepare_payload(self, **payload)` | Objek ServiceClientSend; tidak mengirim request di sini. | `amr_service_client/models/service_client.py:215` |
| `RemoteObjectProxy.call(self, method, args, kwargs=None)` | HTTP client/ORM: Response tanpa raise_for_status; proxy: result atau [] dan raise HTTPError/RuntimeError/JSON error. audience call HTTP tidak diteruskan. | `amr_service_client/models/service_client.py:246` |
| `RemoteObjectProxy.search_read(self, domain=None, fields=None, offset=0, limit=None, order=None)` | Hasil proxy (falsy menjadi []), memakai fallback or; HTTP/envelope/JSON error diteruskan. | `amr_service_client/models/service_client.py:275` |
| `RemoteObjectProxy.read(self, *args, fields=None)` | Hasil proxy (falsy menjadi []); HTTP/envelope/JSON error diteruskan. | `amr_service_client/models/service_client.py:285` |
| `RemoteObjectProxy.search_count(self)` | Hasil proxy count atau [] untuk falsy; error boundary diteruskan. | `amr_service_client/models/service_client.py:292` |
| `RemoteObjectProxy.external_data_callback(self, call_back)` | None; callback sinkron per item; callback/HTTP/JSON error diteruskan. | `amr_service_client/models/service_client.py:297` |
| `ServiceClientFactory.send_request(self, records)` | None; delegates run_action; ensure_one/aksi error diteruskan. | `amr_service_client/models/service_client.py:404` |
| `ServiceClientFactory.run_action_service_client(self, eval_context=None)` | Action terakhir atau None; handler error dapat menelan exception dalam blok HTTP/handle/next, bukan seluruh alur. | `amr_service_client/models/service_client.py:410` |
| `ServiceClientFactory.get_service_client(self, service_code, credential=None, path=None, method=None)` | Objek Python ServiceClient; ValueError endpoint hilang; loader/provider errors. | `amr_service_client/models/service_client.py:473` |
| `ServiceClientFactory.get_remote_object(self, service_code, model_name, credential=None, **kwargs)` | RemoteObjectProxy; error endpoint/credential diteruskan. | `amr_service_client/models/service_client.py:483` |
| `ServiceClientFactory.call(self, service, method, path, params=None, payload=None, headers=None, credential=None, audience=None)` | HTTP client/ORM: Response tanpa raise_for_status; proxy: result atau [] dan raise HTTPError/RuntimeError/JSON error. audience call HTTP tidak diteruskan. | `amr_service_client/models/service_client.py:489` |
| `ServiceClientFactory.get(self, service, path, params=None, headers=None, credential=None, audience=None)` | Response melalui call GET; exception transport/provider diteruskan. | `amr_service_client/models/service_client.py:493` |
| `ServiceClientFactory.post(self, service, path, payload=None, headers=None, credential=None, audience=None)` | Response melalui call POST; exception transport/provider diteruskan. | `amr_service_client/models/service_client.py:499` |
| `ServiceClientFactory.put(self, service, path, payload=None, headers=None, credential=None, audience=None)` | Response melalui call PUT; exception transport/provider diteruskan. | `amr_service_client/models/service_client.py:505` |
| `ServiceClientFactory.delete(self, service, path, headers=None, credential=None, audience=None)` | Response melalui call DELETE; exception transport/provider diteruskan. | `amr_service_client/models/service_client.py:511` |
| `ServiceClientPayload.get_type_display(self)` | String label; mismatch exp/record pada mapping label. | `amr_service_client/models/service_client.py:530` |
| `ServiceClientPayload.custom_render(self, template_str, context)` | String template dengan ekspresi; error ekspresi diganti string kosong, error bentuk template bisa diteruskan. | `amr_service_client/models/service_client.py:535` |
| `ServiceClientPayload.get_payload(self, context=None)` | Dict key/value, duplicate key overwrite; eval/type/random error diteruskan. | `amr_service_client/models/service_client.py:546` |
| `ServiceClientLog.dispatch_send(self)` | Helper: log record jika logging/error atau None; log model: self setelah send sinkron. Penanganan error dapat menutupi error awal. | `amr_service_client/models/service_client_log.py:25` |
| `ServiceClientLog.send(self)` | self setelah menulis state/response log; HTTP/exception ditangkap, error persist di luar handler dapat diteruskan. | `amr_service_client/models/service_client_log.py:30` |
| `ServiceCredential.get_credential_provider(self)` | Objek provider; error loader/factory diteruskan. | `amr_service_client/models/service_credential.py:32` |
| `ServiceCredential.action_config_credential(self)` | Dict action membuka wizard. | `amr_service_client/models/service_credential.py:35` |
| `ServiceCredential.action_test_credential(self)` | Dict notifikasi jika provider tidak error; exception dibungkus UserError dan di-log. | `amr_service_client/models/service_credential.py:49` |
| `ServiceEndpointMixin.open_config_parameter(self)` | Dict action form; dapat membuat parameter sudo; error ORM diteruskan. | `amr_service_client/models/service_endpoint.py:44` |
| `ServiceEndpointMixin.get_value_config_param(self, config_param_name=None, value_without_config_param=None)` | Nilai parameter atau None/fallback; akses parameter sudo. | `amr_service_client/models/service_endpoint.py:56` |
| `ServiceEndpointMixin.get_base_url(self)` | String base tanpa slash akhir. | `amr_service_client/models/service_endpoint.py:99` |
| `ServiceEndpointMixin.get_path_url(self)` | String base_path tanpa slash akhir. | `amr_service_client/models/service_endpoint.py:102` |
| `ServiceEndpointMixin.get_url(self, path=None)` | URL/path gabungan atau nilai compute falsy; bukan validasi host. | `amr_service_client/models/service_endpoint.py:105` |
| `ServiceEndpointMixin.request_headers_default(self, headers=None)` | Dict header default ditambah override caller. | `amr_service_client/models/service_endpoint.py:128` |
| `ServiceEndpointMixin.action_test_connection(self)` | Dict action membuka wizard (tidak menguji koneksi sendiri). | `amr_service_client/models/service_endpoint.py:140` |
| `ServiceEndpointMixin.get_service_client(self, credential=None)` | Objek Python ServiceClient; ValueError endpoint hilang; loader/provider errors. | `amr_service_client/models/service_endpoint.py:155` |
| `ServiceEndpointMixin.get_remote_object(self, model_name, credential=None, **kwargs)` | RemoteObjectProxy; error endpoint/credential diteruskan. | `amr_service_client/models/service_endpoint.py:158` |
| `ServiceAuthFactory.create_service_auth(self, credential)` | Provider termasuk NoneAuth jika kosong; ValueError jika tipe tidak ada di factory. | `amr_service_client/services/auth_factory.py:30` |
| `ServiceCredentialLoaderDatabase.load_credential(self, credential)` | Dict JSON credential pada input sesuai schema; ValueError lookup/source/type/missing; JSON/file/type error diteruskan. Loader database juga merge scopes. | `amr_service_client/services/credential_loader.py:16` |
| `ServiceCredentialLoaderFilePath.load_credential(self, credential)` | Dict JSON credential pada input sesuai schema; ValueError lookup/source/type/missing; JSON/file/type error diteruskan. Loader database juga merge scopes. | `amr_service_client/services/credential_loader.py:31` |
| `ServiceCredentialLoaderEnvJson.load_credential(self, credential)` | Dict JSON credential pada input sesuai schema; ValueError lookup/source/type/missing; JSON/file/type error diteruskan. Loader database juga merge scopes. | `amr_service_client/services/credential_loader.py:40` |
| `ServiceCredentialLoaderEnvPath.load_credential(self, credential)` | Dict JSON credential pada input sesuai schema; ValueError lookup/source/type/missing; JSON/file/type error diteruskan. Loader database juga merge scopes. | `amr_service_client/services/credential_loader.py:52` |
| `ServiceCredentialLoaderConfigPath.load_credential(self, credential)` | Dict JSON credential pada input sesuai schema; ValueError lookup/source/type/missing; JSON/file/type error diteruskan. Loader database juga merge scopes. | `amr_service_client/services/credential_loader.py:65` |
| `ServiceCredentialLoaderParameterJson.load_credential(self, credential)` | Dict JSON credential pada input sesuai schema; ValueError lookup/source/type/missing; JSON/file/type error diteruskan. Loader database juga merge scopes. | `amr_service_client/services/credential_loader.py:78` |
| `ServiceCredentialLoaderParameterPath.load_credential(self, credential)` | Dict JSON credential pada input sesuai schema; ValueError lookup/source/type/missing; JSON/file/type error diteruskan. Loader database juga merge scopes. | `amr_service_client/services/credential_loader.py:90` |
| `ServiceCredentialLoader.get_credential(self, credential)` | Record credential/argumen asli; ValueError lookup; fallback XML-ID bermasalah. | `amr_service_client/services/credential_loader.py:112` |
| `ServiceCredentialLoader.load_cached(self, credential)` | Return load_credential melalui ormcache id/write_date; error loader diteruskan. | `amr_service_client/services/credential_loader.py:122` |
| `ServiceCredentialLoader.load_credential(self, credential)` | Dict JSON credential pada input sesuai schema; ValueError lookup/source/type/missing; JSON/file/type error diteruskan. Loader database juga merge scopes. | `amr_service_client/services/credential_loader.py:125` |
| `ServiceCredentialLoader.get_credential_provider(self, credential)` | Objek provider; error loader/factory diteruskan. | `amr_service_client/services/credential_loader.py:148` |
| `AuthenticationProvider.is_token_expired(self, token, leeway=0)` | Boolean dari exp tanpa validasi signature; DecodeError dianggap expired, exp hilang dianggap belum expired. | `amr_service_client/services/providers.py:38` |
| `AuthenticationProvider.authenticate(self, request_context, audience=None)` | Request-context dict termutasi (base/None no-op); provider spesifik dapat raise key/token/file/HTTP/JSON/signing error. | `amr_service_client/services/providers.py:53` |
| `AuthenticationProvider.test_credential(self)` | Base/static: UserError tidak tersedia; None: None; token providers: dict respons token atau error token. Bukan validasi resource. | `amr_service_client/services/providers.py:56` |
| `NoneAuthProvider.test_credential(self)` | Base/static: UserError tidak tersedia; None: None; token providers: dict respons token atau error token. Bukan validasi resource. | `amr_service_client/services/providers.py:62` |
| `ApiKeyProvider.authenticate(self, request_context, audience=None)` | Request-context dict termutasi (base/None no-op); provider spesifik dapat raise key/token/file/HTTP/JSON/signing error. | `amr_service_client/services/providers.py:68` |
| `BearerProvider.authenticate(self, request_context, audience=None)` | Request-context dict termutasi (base/None no-op); provider spesifik dapat raise key/token/file/HTTP/JSON/signing error. | `amr_service_client/services/providers.py:78` |
| `BasicProvider.authenticate(self, request_context, audience=None)` | Request-context dict termutasi (base/None no-op); provider spesifik dapat raise key/token/file/HTTP/JSON/signing error. | `amr_service_client/services/providers.py:88` |
| `GetJWTTokenProvider.authenticate(self, request_context, audience=None)` | Request-context dict termutasi (base/None no-op); provider spesifik dapat raise key/token/file/HTTP/JSON/signing error. | `amr_service_client/services/providers.py:171` |
| `GetJWTTokenProvider.test_credential(self)` | Base/static: UserError tidak tersedia; None: None; token providers: dict respons token atau error token. Bukan validasi resource. | `amr_service_client/services/providers.py:176` |
| `ClientSecretProvider.authenticate(self, request_context, audience=None)` | Request-context dict termutasi (base/None no-op); provider spesifik dapat raise key/token/file/HTTP/JSON/signing error. | `amr_service_client/services/providers.py:276` |
| `ClientSecretProvider.test_credential(self)` | Base/static: UserError tidak tersedia; None: None; token providers: dict respons token atau error token. Bukan validasi resource. | `amr_service_client/services/providers.py:283` |
| `ServiceAccountProvider.test_credential(self)` | Base/static: UserError tidak tersedia; None: None; token providers: dict respons token atau error token. Bukan validasi resource. | `amr_service_client/services/providers.py:433` |
| `normalize_json(value)` | Nilai JSON-compatible rekursif; formatter/coercion error dapat diteruskan. | `amr_service_client/services/service_client.py:18` |
| `ServiceClient.prepare_request_context(self, path, method=None, params=None, payload=None, headers=None, audience=None)` | Dict kwargs requests berisi auth; error resolver/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:77` |
| `ServiceClient.call(self, method, path, params=None, payload=None, headers=None, audience=None)` | HTTP client/ORM: Response tanpa raise_for_status; proxy: result atau [] dan raise HTTPError/RuntimeError/JSON error. audience call HTTP tidak diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:97` |
| `ServiceClient.get(self, path, params=None, **kwargs)` | Response melalui call GET; exception transport/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:101` |
| `ServiceClient.post(self, path, payload=None, **kwargs)` | Response melalui call POST; exception transport/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:104` |
| `ServiceClient.put(self, path, payload=None, **kwargs)` | Response melalui call PUT; exception transport/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:107` |
| `ServiceClient.delete(self, path, **kwargs)` | Response melalui call DELETE; exception transport/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:110` |
| `RemoteObjectProxy.call(self, method, args, kwargs=None)` | HTTP client/ORM: Response tanpa raise_for_status; proxy: result atau [] dan raise HTTPError/RuntimeError/JSON error. audience call HTTP tidak diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:139` |
| `RemoteObjectProxy.search_read(self, domain=None, fields=None, offset=0, limit=None, order=None)` | Hasil proxy (falsy menjadi []), memakai fallback or; HTTP/envelope/JSON error diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:168` |
| `RemoteObjectProxy.read(self, *args, fields=None)` | Hasil proxy (falsy menjadi []); HTTP/envelope/JSON error diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:178` |
| `RemoteObjectProxy.search_count(self)` | Hasil proxy count atau [] untuk falsy; error boundary diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:185` |
| `RemoteObjectProxy.external_data_callback(self, call_back)` | None; callback sinkron per item; callback/HTTP/JSON error diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:190` |
| `ServiceClientFactory.get_service_client(self, service_code, credential=None)` | Objek Python ServiceClient; ValueError endpoint hilang; loader/provider errors. **UNLOADED.** | `amr_service_client/services/service_client.py:230` |
| `ServiceClientFactory.get_remote_object(self, service_code, model_name, credential=None, **kwargs)` | RemoteObjectProxy; error endpoint/credential diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:235` |
| `ServiceClientFactory.call(self, service, method, path, params=None, payload=None, headers=None, credential=None, audience=None)` | HTTP client/ORM: Response tanpa raise_for_status; proxy: result atau [] dan raise HTTPError/RuntimeError/JSON error. audience call HTTP tidak diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:241` |
| `ServiceClientFactory.get(self, service, path, params=None, headers=None, credential=None, audience=None)` | Response melalui call GET; exception transport/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:245` |
| `ServiceClientFactory.post(self, service, path, payload=None, headers=None, credential=None, audience=None)` | Response melalui call POST; exception transport/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:251` |
| `ServiceClientFactory.put(self, service, path, payload=None, headers=None, credential=None, audience=None)` | Response melalui call PUT; exception transport/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:257` |
| `ServiceClientFactory.delete(self, service, path, headers=None, credential=None, audience=None)` | Response melalui call DELETE; exception transport/provider diteruskan. **UNLOADED.** | `amr_service_client/services/service_client.py:263` |
| `ServiceTokenCache.get_cache(self, key)` | Token tersimpan jika belum expired, selain itu None dan entry dihapus. | `amr_service_client/services/token_cache.py:20` |
| `ServiceTokenCache.set_cache(self, key, token, expires_in)` | None; menulis cache module-global; tools.timedelta perlu QA. | `amr_service_client/services/token_cache.py:28` |
| `ServiceCredentialWizard.action_generate(self)` | Dict action wizard setelah membentuk JSON/file; bukan penerbitan credential. | `amr_service_client/wizards/service_credential.py:48` |
| `ServiceCredentialWizard.action_save(self)` | Dict close setelah menulis JSON ke credential active_id; error ORM diteruskan. | `amr_service_client/wizards/service_credential.py:103` |
| `ServiceCredentialWizard.action_save_to_credential(self)` | Dict close setelah menulis JSON dan source database ke active_id; error ORM diteruskan. | `amr_service_client/wizards/service_credential.py:110` |
| `ServiceEndpointTestWizard.action_test(self)` | Dict action wizard; success bool/status/body diubah. Parse/resolusi sebelum try dapat raise; error HTTP/JSON dalam try ditangkap. | `amr_service_client/wizards/service_endpoint_test.py:29` |

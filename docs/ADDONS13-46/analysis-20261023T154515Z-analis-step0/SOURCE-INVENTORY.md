ADDONS13-46 — Inventaris sumber statis/read-only

Rujukan: [PRD](PRD-DRAFT.md), [UAT](UAT-DRAFT.md), [laporan](ANALYST-REPORT.md), [manifest baru](RESULT.json).

1. Identitas dan metode

S: /home/ubuntu/worktrees/ADDONS13-39-SOURCE
HEAD awal: 6725f802acde636be0b25e2c140d15dccd37b0db; status porcelain kosong (clean).
T: /tmp/ADDONS13-46-target-main
HEAD awal: dae519f29e9c4709dc04796b38148b00d333c58b; status porcelain kosong (clean).
Status akhir dan content recheck dicatat di laporan/manifest. Tidak mengklaim remote freshness.

Untuk SETIAP subprocess Git sejak probe pertama: GIT_NO_LAZY_FETCH=1 GIT_TERMINAL_PROMPT=0 GIT_OPTIONAL_LOCKS=0. Probe rev-parse HEAD dan status --porcelain=v1 --untracked-files=normal pada kedua root exit 0. Kemudian ls-tree -r -z HEAD dan cat-file --batch-check untuk blob teks addon: source 15, target 21, tersedia lokal; tidak ada indikasi missing/fetch. Error/missing/indikasi fetch adalah STOP, bukan alasan retry tanpa guard. Tidak ada fetch, ls-remote, import addon, test, jaringan/DB/Odoo/service.

Pembacaan dibatasi file addon yang diketahui, manifest lokal untuk dependency matrix, AGENTS target, standard lifecycle dan artefak v4. Hash dihitung dari bytes; AST parse hanya data lokal tanpa import/exec. Tidak membaca credential/env/private-key files, tidak menyimpan source/log dump. Nama parameter adalah identifiers, bukan nilai konfigurasi aktual.

2. Hash konten addon

Semua 15 file source berikut byte-identik dengan target (SHA-256 sama). Ini fakta file, bukan bukti instalasi. File helper/consumers/config/ACL/view/controller/wizard dan test target dibaca bermakna; init wrappers ikut inventaris/hash, beberapa hanya AST/import declarations.

Path relatif | SHA-256 source DAN target
amr_resource/__init__.py | e7c766c9d2a830f572ad797e4b9477a75410b1020aecf56bb10df040b63e4228
amr_resource/__manifest__.py | bcff21017293fa250b1d2e38689fc49cceadd853f044c8f237252258f79fb378
amr_resource/controllers/__init__.py | b234a1eaed155b9bba030255424578732e77061f14a4cfa00b79ef4a8a9e5cc7
amr_resource/controllers/main.py | b2513472d548ef722ab4c381b00b2c8d8834ff4af7ebf985fe2f7eee461c95d8
amr_resource/exceptions.py | d92aba23eb87d1b71b4cce300523c7408667cb57c372ba9e2ad4bd2ba1b99682
amr_resource/models/__init__.py | 49f832cbc2270f6e798bb3951295916e8628f6f77d1716dc00d857f9a8bf301c
amr_resource/models/helper.py | 81e0b0afaaedd28e0f1d59b369270d06891eb116033f682397c987164ad1aeea
amr_resource/models/ir_http.py | c3da78e8f54ab622e31f82ec282e4ed61b86850dea77e064a734b5767316a322
amr_resource/models/res_config_settings.py | 13c1011714ea8de63b56897afd8e9b31418caf919ee67cf84b1c97509ca00ca1
amr_resource/models/res_users.py | 850b87415091579e306fcea1680c1bc52ed9ce1dc735edb7c2e21a0d375724eb
amr_resource/security/res_groups.xml | 7f5750f52a13cc03d24d4968fba9105c6068fe3b1e97397662077afb6bd497ad
amr_resource/views/res_config_settings_views.xml | 4dc3cc88a0c4015b58ce7cb6e63800354f399e932c08b65f4a9c0aabe2c2f406
amr_resource/wizard/__init__.py | 2bb8e80861751bab84e7999dc36cdc41f14286316c3814215f73b0abd3780461
amr_resource/wizard/create_user_wizard.py | 8132460ad6a9b8addfc27c32bb0ac0d7b2df7f06a206c68891f1d4370fa4c233
amr_resource/wizard/create_user_wizard.xml | 8f4a833a3512fbff6f5d77a4a1517e28c7779f7b528e10ffdaa3d987d989ce72

Target-only additions, tidak ada pada tracked addon source:
amr_resource/README.md | c6c9b7967bf291b9e9c6ef428a19b70ee682c50ee9fb6654af6c87d993948ee3
amr_resource/docs/developer.md | ad1ebfb1b165879028a39c495eee15b60bfe45f47bb903032a755889b124f113
amr_resource/docs/user.md | 9fbb4a9ede4ffa342354a78abccd475e9bbe112d6086c2f7dd35281e3b950b6a
amr_resource/tests/__init__.py | caec94cadbbfb42da558ea8f280ef829f8ec97501289e08c7c51e4298cf94f2e
amr_resource/tests/test_helper.py | d5afbbfd9917bf7f1b72cd1a127d3e13f03a438b14fb8520911f618748b035f0
amr_resource/tests/test_contracts.py | 7c34ac045e8977cd3002e9dd3ce2c77d213f9beb8a0d4e50cc380c3b0eb482fb

3. Fakta lokasi dan call-path terverifikasi

Seluruh T: di bawah berada pada pin target; karena hash sama, lokasi file produksi juga berlaku pada S:. Tidak menyalin raw source.

F-01 CONFIG — T:amr_resource/models/helper.py:20-37. is_local_issuer membandingkan web.base.url langsung; get_issuer/get_audience menyelesaikan key parameter yang dipilih lalu fallback; get_audiences mengembalikan satu audience dan tidak memakai issuer. T:amr_resource/models/res_config_settings.py:9-29,50-78 memberi selector, computed preview tanpa fallback identik helper dan action parameter.
F-02 METADATA/JWKS — T:amr_resource/models/helper.py:40-51. get_oidc_config dan get_jwks_data GET well-known berbeda; raise HTTP, JSON, tanpa timeout eksplisit di callsite. AST addon produksi tidak menemukan explicit call ke get_jwks_data; test mengaksesnya lewat bound method pada T:amr_resource/tests/test_helper.py:98-113. Absence call statis bukan bukti tidak ada dynamic/external caller.
F-03 GENERATION — T:amr_resource/models/helper.py:53-73. encode → generate_token → get_oidc_config → token_endpoint POST; response JSON/access_token wrapper. Issuer aliases dan credential tuple seperti PRD. Tidak memanggil get_issuer di jalur ini.
F-04 INTROSPECTION — T:amr_resource/models/helper.py:83-110. direct url melewati Discovery; jika absent, iss caller/unverified decode → get_oidc_config → introspection_endpoint → GET body data. validate_hs → introspect_token → active truthiness saja pada kode cabang tersebut. Tidak mengekstrapolasi policy server introspection yang UNKNOWN.
F-05 SIGNATURE/CLAIMS — T:amr_resource/models/helper.py:114-149. validate → header alg; HS → validate_hs; selain HS → unverified payload iss → metadata → PyJWKClient(jwks_uri) → signing key → jwt.decode dengan algorithms=[alg], issuer dari payload, audience get_audiences. kid/alg ditambahkan jika tidak ada pada payload hasil. get_jwks_data BUKAN jalur validasi ini. Tidak menilai versi/default cache/timeout/required time claims library tanpa runtime/library inspection terotorisasi.
F-06 CLASSIFICATION — T:amr_resource/models/helper.py:76-80,20-21. is_local_token unverified decode → is_local_issuer; tidak membuktikan token valid. Base validate tidak memiliki local skip; override addon lain tidak diinspeksi ulang/diterima.
F-07 RESOLUTION — T:amr_resource/models/helper.py:151-193. get_validate_user validate lalu payload-or-None, BUKAN user record. get_user_token_login validate → get_user_match; get_uid → get_user_match langsung; is_user_match → get_uid. Matching email(login/email), sub(login), lalu machine include active False; sudo limit=1. Uniqueness/eligibility/provenance bukan jaminan dari struktur ini.
F-08 AUTH CONSUMERS — T:amr_resource/models/ir_http.py:42-108. machine bearer / params token → get_validate_user → get_user_match → Unauthorized bila kosong → update request uid/token/payload hanya bila UID berubah. user_or_param mencoba session, params, bearer dan menelan exception dua cabang pertama. T:amr_resource/models/ir_http.py:14-39 set_session terpisah; :126-139 get_jwt_payload default {}, check_scope no-op. Jangan menyebut scope enforced.
F-09 USER CONTEXT — T:amr_resource/models/res_users.py:48-55,79-95. decode → helper.decode → get_uid → current-user equality; with_access_token_context marker short-circuit, bearer required jika belum marked, validate=True via helper.validate, False dari ir.http payload, lalu get_uid. T:amr_resource/models/res_users.py:14-26 machine-user environment dapat su=True; bukan dipanggil otomatis oleh setiap auth method.
F-10 MANIFEST/ACCESS/VIEW — T:amr_resource/__manifest__.py:9-15 versi 13.0.0.0.8, depends base/web/base_setup, data group/settings/wizard. Inventaris tracked addon tidak memuat ir.model.access.csv atau ir.rule file; XML group bukan ACL efektif. T:amr_resource/security/res_groups.xml:3-26 noupdate groups + inactive machine template. T:amr_resource/views/res_config_settings_views.xml:8-30 ERP Manager visibility, audience/freeze/edit; issuer selector tidak ada pada view. Absence ACL lokal bukan bukti public access/deny secara runtime.
F-11 HTTP BOUNDARY — T:amr_resource/controllers/main.py:51-95 route decorators user_or_param untuk redirect/access URL, machine untuk connection; :98-106 machine JSON call_kw → check_method_name → Odoo call_kw. Declarative call-path bukan HTTP/ACL/MRO evidence. T:amr_resource/exceptions.py:16-36 helper error JSON bukan bukti global exception handler.
F-12 WIZARD — T:amr_resource/wizard/create_user_wizard.py:17-37 login duplicate check, create user dengan share/group template, action form; tidak copy active eksplisit. T:amr_resource/wizard/create_user_wizard.xml:3-25 form, tanpa action/menu entry pada file itu. Tidak mengusulkan rewrite wizard.
F-13 REGISTRY UNKNOWN — T:amr_resource/models/__init__.py:3-6 hanya helper/ir_http/res_users/settings; AST seluruh Python addon kedua pin menemukan _name amr.resource.helper dan create.user.wizard, bukan oidc.issuer.register/audience. Absence assertion dibatasi addon yang diperiksa, bukan semua modul/core/database.
F-14 LOGGING — T:amr_resource/models/helper.py:117-121 error header mencatat token mentah. Baseline conditional risk, tidak menggunakan token nyata atau merekam raw log.

4. Definisi test aktual — semuanya NOT RUN

T:amr_resource/tests/test_helper.py:11-28 ResourceCase mewarisi SavepointCase, helper dari registry; socket/connect dan requests Session guard serta mock logger. Guard yang ada tidak membuktikan DNS sepenuhnya blocked; harness baru wajib menguji resolver DNS juga.
T:amr_resource/tests/test_helper.py:38-71 karakterisasi config; :73-96 extraction precedence; :98-146 metadata/JWKS/generation/wrappers; :148-185 introspection/HS dan audience tidak dipanggil; :187-224 non-HS memock jwt.decode/PyJWKClient dan memeriksa error/logging; :226-242 user matching termasuk inactive machine. Mock decode assertions bukan cryptographic signature evidence.
T:amr_resource/tests/test_contracts.py:26-61 settings/view static assertions; :63-140 direct real auth bodies dengan helper/boundary mocks; :147-225 user predicates/context/session; :227-290 direct controller/error calls (bukan routing/ACL); :292-349 ORM wizard/seed/manifest/import assertions. Ini Odoo DB-dependent suite, bukan unittest standalone yang tersedia tanpa registry. Test behavior lama yang memvalidasi unsafe baseline perlu dibedakan dari regression expectation baru.
T:amr_resource/tests/__init__.py:1-2 mengimpor kedua suite. Tidak import atau execute paket selama analisis.

5. Target/module matrix — fakta repository, bukan installation

AST manifest top-level lokal dibaca tanpa import. Target mempunyai empat manifest addon: amr_resource, amr_token, amr_oidc, amr_service_client.

Addon/grup | Source manifest | Target manifest | Ownership / claim
amr_resource | ada | ada | hanya ini in-scope; target QA effective installation UNKNOWN
amr_token | ada, direct amr_resource dependency | ada, direct dependency | ADDONS13-38; overrides/MRO runtime UNKNOWN
amr_oidc | ada, depends amr_token | ada, depends amr_token | Discovery ADDONS13-38/39; client validation ADDONS13-48
amr_service_client | ada, direct dependency | ada, direct dependency | ADDONS13-49; tidak mengklaim cache kompatibel
amr_auto_login / amr_mobile / amr_oidc_client / amr_resource_jwt / amr_signature | ada, direct dependency | tidak ada | ADDONS13-50/51/53/54/55; runtime external consumers UNKNOWN
amr_oauth | ada, tidak direct amr_resource dependency | tidak ada | ADDONS13-52; source-only presence bukan installed evidence
amr_auth_qr / amr_jsonrpc_jwt / amr_user_public_key | ada, direct dependency | tidak ada | historical context; tidak memberi pekerjaan baru/compatibility claim

Source direct dependents tepat: amr_auth_qr, amr_auto_login, amr_jsonrpc_jwt, amr_mobile, amr_oidc_client, amr_resource_jwt, amr_service_client, amr_signature, amr_token, amr_user_public_key. Target direct dependents hanya amr_service_client dan amr_token. Matriks tidak membaca credential-bearing config atau deploy targets.

6. Provenance dan unknown

Canonical lifecycle dibaca lokal; SHA-256 681b54f76cf8dba3478cff0d0866130b13008c18e013f059d226d349d949ddb6. T:AGENTS.md:7-15 menetapkan Odoo 13/Python 3.7, bukan executable terpasang. Python 3.7.9 berasal dari UAT v4, belum dikonfirmasi sebagai runtime target.

Dokumentasi target membawa provenance/gate historis sendiri, misalnya T:amr_resource/README.md:7-26 dan T:amr_resource/docs/developer.md:127-134; tidak dipromosikan menjadi status task sekarang. v4 dan check Lead dibaca lokal; RESULT historis mengaku v3 dan hash tidak cocok bytes v4 saat ini. Semua enam file historis di-hash sebelum/sesudah; manifest baru tidak memperbaiki manifest lama.

Unknown: current Plane state, remote refs, installed modules/MRO/ACL, DNS/TLS, library versions/implicit PyJWKClient cache, actual Odoo runtime, served routes, token profile dan keputusan policy yang pending. Tidak ada klaim exploitability/deployment/security clearance. Tidak ada sumber eksternal di-fetch; klaim eksternal historis v4 tidak dianggap verifikasi baru.

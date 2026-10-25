# PRD ADDONS13-48 — Konsolidasi OIDC/Token dan OAuth Grants

Versi: r3 — PRD pertama setelah keputusan scope final percakapan.
Status: DRAFT FOR LEAD REVIEW. Keputusan scope Owner sudah dicatat; dokumen belum acceptance Lead.
Deliverable sesi ini: PRD saja. Tidak membuat dokumen UAT dan tidak menjalankan implementasi/test.

## 1. Ringkasan produk

ADDONS13-48 mengonsolidasikan seluruh fungsi addon amr_token ke amr_oidc, memisahkan ownership provider dari resource verification, mengganti API utama menjadi encode/decode, menyediakan self-provider internal tanpa outbound HTTP ke server sendiri, dan mengganti scalar Authorized Party registry menjadi child rows.

Instalasi yang didukung hanya fresh installation. Grant target:

- client_credentials untuk machine-to-machine, tanpa refresh token.
- authorization_code dengan PKCE S256 untuk authorization user dan penerbitan refresh token pertama.
- refresh_token untuk pembaruan token user, rotation single-use dan replay protection.

Password grant dibatalkan oleh Owner. Request grant_type=password wajib ditolak; bukan fitur disabled yang dapat diaktifkan melalui setting.

Penambahan authorization_code adalah OAuth authorization flow, bukan otomatis implementasi OIDC login lengkap. ID Token, implicit flow, OIDC Discovery success dan public/native client support tidak masuk release ini. Profil release dibatasi confidential clients, konsisten dengan paket client-auth yang telah diterima. Batas ini adalah pilihan desain minimum PRD, bukan klaim PKCE hanya berlaku pada confidential clients.

## 2. Dasar keputusan dan precedence

### 2.1 Keputusan Owner yang mengikat

| ID | Keputusan berlaku |
| --- | --- |
| O01 | Task yang benar ADDONS13-48, bukan ADDONS13-46 |
| O02 | Seluruh fungsi amr_token masuk ownership amr_oidc; generation/acquisition keluar dari implementasi base amr_resource |
| O03 | Helper baru amr.oidc.helper; model key tetap amr.public.key, ownership amr_oidc |
| O04 | Public encode mengembalikan access-token string; resource decode mengembalikan verified claims; metadata melalui exchange API/HTTP yang terpisah |
| O05 | Fresh install saja, tanpa upgrade/migration existing DB |
| O06 | Self-provider database Odoo yang sama melalui explicit binding, internal calls, full checks, no silent fallback |
| O07 | azp exact dari oidc.client.name, semantik berbeda client_id; aturan uniqueness/value C4 diterima; child oidc.issuer.register.azp |
| O08 | azp ANY exact-match; parent single client_id tetap diverifikasi independen |
| O09 | URL endpoint dipertahankan; rename API utama; aliases hanya bila real callers memerlukan; dormant assets tidak otomatis aktif |
| O10 | Paket client_credentials C3 diterima: confidential client, Basic/post exclusive, eligible machine account, RS256 at+jwt, TTL 3600, tanpa refresh/id_token |
| O11 | Password grant dibatalkan untuk mengikuti standard security; bukan risk exception |
| O12 | D2 diterima sejauh relevan: eligibility, stable user identity/binding, no auth/MFA bypass, TTL ceiling dan rate-limit proposal |
| O13 | D3 diterima: opaque refresh >=256-bit entropy, digest storage, binding, 14-day absolute/24-hour idle, strict rotation, family replay revocation |
| O14 | D4 diterima: metadata-bearing exchange API terpisah; encode tetap string dan tidak membuang refresh/replacement token |
| O15 | Jawaban klarifikasi Owner: tambahkan authorization_code + PKCE sebagai sumber refresh token awal |
| O16 | Buat PRD terlebih dahulu, tanpa UAT |

O11/O15 menggantikan ketentuan r2 bahwa refresh pertama berasal dari password grant. Ketentuan D2 tentang pengecekan password pada token endpoint tidak berlaku lagi: user authentication berlangsung melalui login/session server Odoo pada authorization flow. Tidak ada endpoint baru yang menerima username/password untuk token exchange.

### 2.2 Batas dokumen

Spesifikasi detail di bawah adalah rancangan normatif untuk Developer dan review Lead, bukan seluruhnya kutipan keputusan Owner atau bukti perilaku existing. Tidak ada pertanyaan produk tambahan yang harus dijawab sebelum PRD ini diserahkan. Verifikasi baseline, runtime, dependency dan mekanisme transaksi tetap merupakan readiness teknis, bukan dianggap sudah terbukti.

Dokumen historis tetap dipertahankan:

- /home/ubuntu/docs/reports/ADDONS13-48/RINGKASAN-DAN-KONFIRMASI-r1.md
- /home/ubuntu/docs/reports/ADDONS13-48/ANALISIS-DAN-KONFIRMASI-r2.md
- /home/ubuntu/.hermes/profiles/analis/plans/2026-10-25-ADDONS13-48-analisis-ulang-r1.md

Jika berbeda, keputusan Owner terbaru dan PRD r3 ini menjadi rujukan scope saat review; acceptance dokumen tetap milik Lead.

## 3. Masalah, pengguna dan tujuan

### 3.1 Masalah

- Provider functions tersebar antara amr_resource, amr_token dan amr_oidc; module ownership, helper contracts dan endpoint inheritance saling terkait.
- Existing encode/generation mempunyai return string/dictionary/tuple yang berbeda. Rename tekstual dapat merusak callers.
- Local-token classification dapat memanggil validation yang memanggil classification kembali; test yang memock classification tidak membuktikan original chain aman.
- Existing provider generation belum dijamin memenuhi strict resource verifier.
- Token dispatcher masih menolak grants; existing authorization endpoint masih fail-closed. Private helper bodies bukan bukti capability siap.
- Existing refresh schema/lifecycle tidak cukup untuk client binding, rotation, replay detection dan expiry yang benar.
- Scalar azp tidak mendukung daftar Authorized Parties serta memengaruhi snapshot/revision/access guards.

### 3.2 Pengguna

- Trust administrator: mengelola issuer/policy/binding/audience/Authorized Party.
- Provider administrator: mendaftarkan client, redirect URI, scope/audience, key dan grant permissions.
- Machine client: memperoleh access token melalui client_credentials sebagai explicit service account.
- Eligible internal user: menyelesaikan native Odoo authentication/MFA lalu menyetujui authorization client.
- Confidential application backend: menyimpan PKCE verifier/state, menukar code dan merotasi refresh token.
- Developer/Lead: mengimplementasikan/mereview ownership dan kontrak yang dapat diperiksa tanpa menebak.

### 3.3 Tujuan

G01. Dua addon fungsional dengan dependency acyclic amr_oidc -> amr_resource.
G02. Fresh installation provider tidak membutuhkan functional addon amr_token.
G03. End-to-end authorization_code + S256 -> access/refresh -> rotation bekerja melalui kontrak yang sama pada HTTP dan authorized internal service.
G04. Client_credentials tetap sederhana: access only, machine identity, tanpa refresh.
G05. Self-provider mengganti transport, bukan mengganti trust/identity/authentication checks.
G06. Child azp konsisten pada runtime policy, ACL, revision/concurrency dan current-schema snapshots.

## 4. Scope

### In scope

- Seluruh functional ownership amr_token dipindah ke amr_oidc: engine, key, helper, settings/UI/menu/ACL/controllers, tests dan product docs.
- Canonical helper/API, consumer-callsite updates yang diperlukan pada source yang tersedia, safe compatibility ledger.
- Local provider binding, supported external verification tetap, guarded external acquisition bila dipakai profile.
- Confidential-client client_credentials, authorization_code + PKCE S256, refresh_token.
- Native login/session integration, authorization transaction dan explicit consent UI.
- Strict redirect registration, client auth, user/service identity, scopes/audience, replay/expiry/credential protection.
- Current-schema policy snapshot/restore dan session invalidation yang dijelaskan di PRD ini.
- Fresh-install product documentation. Acceptance criteria PRD, tanpa dokumen UAT pada tahap ini.

### Out of scope

- Password/ROPC, implicit, authorization response_type=token, client assertion grants, private_key_jwt, mTLS client auth, device grant.
- Public clients, SPA/native-client registration dan loopback/custom-scheme redirect exceptions.
- ID-token issuance, OIDC claims/login compliance penuh, Discovery/RFC8414 success, dynamic client registration.
- Upgrade existing DB, legacy token/data conversion, installed-module ownership migration, automatic uninstall/reinstall atau existing-data cleanup.
- Menjalankan QA/UAT, deployment, perubahan Plane, PR/merge, atau provisioning infrastruktur dalam sesi PRD.
- Multi-client_id trust allowlist per issuer; single parent client_id tetap.
- Universal external-consumer compatibility, provider cache redesign, arbitrary stored Python execution atau scope/RBAC engine baru di resource.

## 5. Bukti source dan batas baseline

Source root yang dibaca:

`/home/ubuntu/worktrees/ADDONS13-48-odoo_13_addons`

References path:line relatif ke root itu. Local HEAD yang pernah dibaca pada rangkaian analisis: 153bd6cdb4552f3a698efbc08d33963569cd56d5. Ini tidak membuktikan working tree bersih, file identik dengan commit, atau pull/main freshness. Lead/Developer harus menetapkan baseline/candidate aktual sebelum Coding.

| S-ID | Bukti source | Implikasi |
| --- | --- | --- |
| S01 | amr_oidc/__manifest__.py:12; amr_token/__manifest__.py:11 | Dependency existing masih melalui amr_token |
| S02 | amr_resource/models/helper.py:301–329; amr_token/models/helper.py:245–308 | Return shape generation berbeda |
| S03 | amr_token/models/helper.py:46–61; amr_resource/models/helper.py:331–333 | Conditional recursion hazard melalui classification/validation |
| S04 | amr_resource/models/helper.py:335–372,389–470 | Resource meminta RS256, at+jwt, policy claims/provenance |
| S05 | amr_token/models/helper.py:183–188; amr_oidc/controllers/main.py:14–19,29–42 | Grant dispatcher dan authorization existing belum mendukung flow target |
| S06 | amr_oidc/models/oidc_authorization_code.py:15–31 | Code existing hanya code/client/user/redirect/scope/expiry/used; belum PKCE dan atomic lineage |
| S07 | amr_oidc/models/oidc_client.py:61–98 | Redirect validator menerima beberapa kondisi secara luas dan membandingkan normalized URI tanpa query |
| S08 | amr_oidc/models/oidc_client.py:114–126 | Creator memasukkan string self.client_id ke field tujuan Many2one; perlu ORM-correct foreign key |
| S09 | amr_oidc/models/helper.py:221–231; models/oidc_refresh_token.py:87–105 | Validator-call mismatch dan expiry predicate '< now' pada source |
| S10 | amr_oidc/security/ir.model.access.csv:2–7; models/oidc_client.py:25–59 | Refresh ACL luas, ordinary client reads, secret/name/client constraints perlu dibenahi |
| S11 | amr_resource/models/trust_registry.py:18–25,230–341,648–775,855–856 | Child azp harus ikut guard/locking/revision/snapshot; scalar masih dipakai |
| S12 | amr_resource/models/helper.py:476–488,553–570 | User harus eligible, bound dan memakai verified provenance |
| S13 | amr_service_client/services/providers.py:203–237 | Known consumer mengirim form-body client credentials dan optional audience/scope |
| S14 | amr_resource/models/ir_http.py:84–93 | check_scope masih stub; scope issuance bukan bukti endpoint authorization |

Seluruhnya static inspection; bukan reproduksi runtime, security exploit atau test PASS.

## 6. Architecture dan component ownership

### FR-01 — Module composition

- amr_resource tidak bergantung pada amr_oidc; resource-only install tidak mereferensikan provider models yang absen.
- amr_oidc bergantung langsung pada amr_resource dan dependency framework yang benar-benar dipakai, termasuk base_setup bila moved settings memerlukannya.
- Tidak ada runtime Python/controller import atau menu/settings reference yang mengharuskan functional amr_token.
- Dormant legacy views/models tetap unloaded atau di-retire lewat disposition ledger; jangan auto-enable unresolved amr.token references.
- Source namespace/key/config literal yang sengaja dipertahankan dicatat; acceptance bukan sekadar nol string amr_token.

### FR-02 — Services

- amr.oidc.helper menjadi public provider/acquisition API.
- Private token engine menangani signing/material yang telah diotorisasi, bukan arbitrary claims signing RPC.
- amr.resource.helper.decode menangani full verification, provenance dan resolver boundary.
- HTTP controllers hanya parsing, transport-level auth extraction, serialization dan framework redirects. Business logic berada pada models/services.
- Tidak ada monkey patch; memakai Odoo ORM/_inherit sesuai AGENTS. Privileged operations harus sempit dan dijelaskan; sudo seluruh pipeline tidak dianggap authorization.

### FR-03 — Local provider binding

Desain release: satu canonical local provider per database, model baru oidc.provider dengan issuer required exact HTTPS, active flag, signing_key_id -> amr.public.key dan verification_key_ids untuk authorized public verification material. Database invariant mencegah lebih dari satu canonical local provider.

Extension amr_oidc pada oidc.issuer.register menambahkan local_provider_id dan mode verification_source=self_provider. Fields provider hanya tersedia jika addon terpasang. Mode ini menggantikan kebutuhan fake JWKS/loopback URL, bukan menonaktifkan policy.

- Selected registry issuer harus exact-match canonical provider issuer.
- Signing key harus termasuk authorized verification keys, active, RS256, is_signing dan belum expired bila expiry ada; RSA minimal 2048 bit.
- Pemilihan signer eksplisit; tidak first-row search. Private material melalui approved key-source loader; unsupported/unavailable source fail closed.
- Binding/provider/key policy changes mengubah revision yang dipakai verification dan authorization/session rechecks.
- Snapshot extension menyimpan explicit stable references/identity, bukan private material.
- Shared host, request Host header, local_key_ref, unverified JWT iss, atau caller-supplied DB tidak membuktikan self-provider.

## 7. Identitas, client, audience dan Authorized Party

### FR-04 — Confidential client registration

Setiap oidc.client memiliki:

- client_id string required/indexed/global exact unique termasuk archived; reserve prefix user: untuk menghindari client/user subject collision.
- name sebagai azp: required/indexed, maksimal 1024 karakter, global exact-case unique termasuk archived.
- is_confidential=True untuk client aktif release ini.
- Explicit allowed_grants subset dari client_credentials, authorization_code, refresh_token; fresh default tidak mengizinkan grant sampai admin mengonfigurasi.
- Protected client-secret verifier hash; tidak raw readable secret. Secret baru ditampilkan sekali pada protected admin issuance/reset action.
- user_id service account eksplisit bila client_credentials diaktifkan, tanpa default user ID 1. Untuk user flow, subject bukan user_id service account client.
- redirect_uri_ids yang terdaftar untuk authorization_code; audience_ids dan scope policy yang eksplisit.
- auth_epoch yang naik pada secret reset/disable atau security-significant client change; tidak menerima caller epoch.

Basic preferred; client_secret_post untuk compatibility. Kedua mekanisme tidak boleh digunakan bersamaan. Repeated credentials, query credentials, malformed Basic dan unsupported auth method ditolak; tidak fallback body setelah Basic invalid. OAuth Basic form-encoding/decoding mengikuti RFC6749 §2.3.1.

### FR-05 — azp value semantics

- Plain name atau absolute http/https URL dengan host valid; query boleh, userinfo/raw #/fragment tidak, termasuk trailing '#'.
- Tidak boleh whitespace/control/backslash; tidak trim/lowercase/percent-decode/remove slash atau query secara diam-diam.
- '%23' pada path adalah literal encoded value, bukan raw fragment delimiter.
- URL adalah identifier, tidak di-fetch atau diperiksa DNS; tidak memakai SSRF endpoint validator untuk identitas azp.
- Claim azp selalu authenticated client.name; tidak fallback client_id dan tidak berasal dari request/user display name.
- Name change adalah identity change; jangan auto-trust value baru atau otomatis mengubah allowlist registry.
- Semantik ini adalah application access-token profile, bukan azp ID Token OIDC.

### FR-06 — Registry child dan policy

Model oidc.issuer.register.azp, label Authorized Party:

| Field | Kontrak |
| --- | --- |
| issuer_id | Required/indexed Many2one ke oidc.issuer.register; ondelete=cascade |
| value | Required Char, aturan literal valid yang sama untuk configured azp |
| Constraint | unique(issuer_id,value), concurrency-safe |
| Parent | azp_ids One2many; scalar parent azp tidak lagi active runtime truth |
| Access | Inherit amr.resource.registry.access; trust admin guards dan record rules |

Claim tetap satu string; ANY exact-match terhadap selected issuer children. Array/empty/wrong type/cross-issuer value ditolak. Missing mengikuti allow_missing_azp; present claim dengan empty allowlist ditolak. Parent required azp tidak boleh aktif tanpa child.

Direct child create/write/unlink/reparent harus memeriksa kedua parent bila berubah, memakai policy locks/revision/audit dan tidak meninggalkan active required parent kosong. Tambahkan child pada policy-child model/table registry. Current-schema snapshot menyimpan sorted exact azp values; restore dengan revision guard, inactive parent dan integrity checks. Tidak mengonversi legacy snapshots/data existing dalam task fresh-only.

Parent client_id tetap satu dan exact-check independen dari azp/audience. Satu issuer global tidak otomatis menerima dua local OAuth client IDs; admin harus memahami limitation ini, bukan membuat duplicate issuer rows atau menghapus check.

### FR-07 — Audience dan scope

- oidc.client.audience: client_id Many2one, value required exact, is_default boolean; unique(client_id,value); tepat satu default untuk client yang mengaktifkan issuance.
- oidc.client.scope: client_id Many2one, value required single scope-token, is_default boolean; unique(client_id,value). Empty default scope boleh berarti tanpa scope; bukan wildcard.
- Optional audience request harus memilih satu exact approved value. Absent -> explicit default; tidak ada first-row inference. Audience bukan otomatis client_id/name.
- Scope request string space-delimited sesuai RFC6749 scope-token grammar, case-sensitive, tanpa duplicate/unknown tokens. Absent -> explicit default scopes; explicit empty -> empty scope jika policy mengizinkan.
- User flow juga memerlukan explicit consent dan user/client authorization; refresh tidak memperluas original grant atau current policy.
- Tidak menerima openid/offline_access sebagai janji OIDC semantics. Refresh permission dikontrol explicit client grant configuration dan user consent, bukan nama scope yang diam-diam mengaktifkan OIDC.
- Issued scope bukan implementasi resource permission engine. Existing user ACL/record rules tetap berlaku; check_scope stub tidak boleh diklaim sebagai enforcement.

### FR-08 — Principal

- Machine: sub=client.client_id, binding exact issuer+sub -> eligible service user.
- User: immutable subject user:<UUID> yang diprovision oleh authorized identity administration; tidak user login/email, numeric uid request, atau service account client. Reserve prefix user: pada client registration.
- Trust binding dibuat eksplisit sebelum authorization dapat berhasil, bukan auto-enrollment dari token request atau consent.
- Eligible user aktif/internal, bukan superuser/public/portal, company eligible, dan subject-binding unik. User authentication melalui complete native Odoo session/auth/MFA policy. Tidak memperkenalkan email/login fallback sendiri atau password-verification shortcut.
- Authorization code dan refresh mempertahankan principal yang sama. Caller tidak dapat memilih sub/uid/company untuk mengganti principal.
- User deactivation/password/auth-policy/security-epoch change membatalkan user token sessions yang relevan. Browser logout tidak diasumsikan logout-all aplikasi.

## 8. Authorization Code + PKCE

### FR-09 — Authorization request

GET /oidc/authorize dan alias /oidc/auth menerima:

| Input | Requirement |
| --- | --- |
| response_type | Required exact code; token/implicit/other ditolak |
| client_id | Required exact registered active confidential client |
| redirect_uri | Required exact salah satu registered URI |
| code_challenge | Required S256 challenge, 43 base64url chars tanpa padding dan valid SHA256-sized decoded bytes |
| code_challenge_method | Required exact S256; plain/missing/unknown ditolak |
| state | Required nonempty <=1024 chars; dikembalikan identik setelah satu transport decode, escaped/encoded saat response |
| scope | Optional, sesuai client policy dan consent |
| audience | Optional extension, exact approved selection |

Tidak menerima secret, username/password, code_verifier, uid, arbitrary issuer atau token claims pada authorization query.

Redirect registration hanya absolute HTTPS, no userinfo/fragment/wildcard; exact full-string matching termasuk query/trailing slash. Query statis boleh, tetapi registered URI tidak boleh membawa reserved response parameters code/state/error/iss. Tidak normalize/canonicalize untuk membuat mismatch lolos. redirect_path/web_base_url helper lama tidak memberi bypass registration. Tidak fetch redirect URL.

Invalid client/redirect -> local sanitized 400, tidak redirect ke untrusted URI. Error lain setelah redirect tervalidasi -> authorized redirect dengan error dan state; authorization denial memakai access_denied. Tidak mengirim access/refresh token melalui browser redirect atau fragment.

### FR-10 — Login, authorization transaction dan consent

- Parse/validate request sebelum login redirect. Simpan canonical transaction server-side, random opaque transaction handle >=256-bit, expiry 300 detik, bind originating browser session dan exact request/client/PKCE/state/audience/scope.
- Jika user belum fully authenticated, redirect ke native Odoo login dengan server-owned same-origin return target. Jangan menerima arbitrary next URL atau serialize secret/full grant state ke login query.
- Native login tetap dapat menggunakan password/MFA pada authorization server; ini tidak menghidupkan OAuth password grant. Token endpoint tidak menerima user password.
- Setelah login, rebind transaction secara aman ke completed/rotated session, recheck user/client/profile/redirect/policy. Pre-auth transaction tidak menjadi bearer authorization yang dapat dipakai dari browser/session lain.
- Tampilkan explicit consent: client identity/azp, authenticated user, audience, requested scopes dan pemberian refresh access bila enabled. Tidak auto-consent atau membuat subject binding otomatis.
- POST /oidc/authorize_continue memakai native CSRF protection, authenticated user dan one-time transaction handle. Approve/deny hanya dari bound session. GET tidak melakukan approval side effect.
- Transaction expire/change/duplicate/replay -> reject; perubahan user setelah consent membatalkan transaction. Perubahan policy saat login/consent harus terdeteksi.
- UI output di-escape; no third-party resources, frame-ancestors none, Referrer-Policy no-referrer, no-store pada authorization/consent pages dan responses yang membawa code.

### FR-11 — Authorization code

Setelah consent valid:

- Generate opaque random code >=256-bit entropy; simpan SHA-256 digest, bukan plaintext code; response browser mendapat raw code sekali.
- Bind issuer/provider, exact client record/OAuth ID, user stable subject, exact redirect URI, approved audience/scopes, S256 challenge/method, policy/auth epochs dan consent proof.
- TTL 300 detik sejak issue, single use, now < expires_at. Expiry tidak bergantung cleanup cron.
- Redirect 303 ke registered URI dengan code dan exact state; tambahkan iss canonical provider sebagai issuer identification response. Client contract harus verify issuer/state sebelum exchange.
- Code store tidak readable/writable oleh ordinary users/portal/public; jangan menaruh raw code/verifier pada logs.

### FR-12 — Code redemption

POST /oidc/token: grant_type=authorization_code, code, redirect_uri, code_verifier; client auth wajib.

- Authenticate exact client dan verify grant permission.
- Require code bound ke issuer/client/redirect dan unused/unexpired; full exact redirect match dengan saved authorization value.
- Verifier 43–128 ASCII unreserved ALPHA/DIGIT/-/./_/~ sesuai RFC7636. Hitung BASE64URL-NOPAD(SHA256(ASCII(verifier))) dan constant-time compare dengan stored challenge. Tidak menyimpan raw verifier.
- Missing/malformed verifier -> invalid_request; proof mismatch/bad/expired/reused code -> invalid_grant. PKCE dan client secret keduanya wajib; bukan alternatif.
- Recheck current authenticated-user eligibility, binding, client/profile/key policy dan consent bounds. Tidak menukar user berdasarkan caller/session token endpoint.
- Atomically consume code, create user authorization/token session, issue access and permitted initial refresh. Signing/storage failure tidak meninggalkan partially consumed code dengan usable orphan tokens.
- Concurrent redemptions tidak menghasilkan dua successful issuances. Proven same-client code replay dengan valid proof menolak request dan membatalkan derived token session/family. Wrong client/random code tidak boleh mencabut session orang lain.
- Replay invalidation harus persisted walau response 400; jangan exception rollback yang membatalkan revoke.

## 9. Client Credentials dan Access Token

### FR-13 — Client credentials

grant_type=client_credentials; optional scope/audience sesuai policy, authenticate confidential client, require allowed grant dan explicit eligible service account/binding.

Tidak memakai user password, user browser session atau arbitrary user selection. Response hanya access metadata, tanpa refresh/id_token. Tidak memulai user token session hanya untuk menyamakan implementation dengan user flow.

### FR-14 — Access-token profile

| Bagian | Requirement |
| --- | --- |
| Header | typ=at+jwt; alg=RS256; kid exact authorized signer |
| iss | Exact canonical provider issuer, bukan request Host |
| sub | Machine client ID atau stable bound user subject sesuai grant |
| client_id | OAuth client ID dari authenticated client |
| azp | Exact client.name; required untuk locally issued tokens |
| aud | Single selected authorized audience string pada issuance release ini |
| iat/exp | Integer server timestamps; exp=iat+TTL |
| jti | Fresh random unique identifier setiap issuance |
| scope | Canonical granted scope string; tidak arbitrary request claims |
| sid | Required untuk locally issued user tokens; token-session public opaque identifier, bukan bearer refresh token |

TTL default 3600 detik, configurable integer 1..3600. Tidak HS fallback, unverified decode-as-validation, ID Token acceptance, arbitrary algorithm or claims override. Raw request password/client secret/code/verifier/refresh tidak ada pada access claims.

Public verification keys tidak mengungkap private material. Rollover explicit: only selected signer issues; old public keys dapat tetap authorized untuk unexpired tokens. Inactive/untrusted key tidak digunakan lewat fallback.

## 10. Refresh dan token-session lifecycle

### FR-15 — First issuance dan binding

Refresh awal hanya dari authorized authorization_code redemption dengan client refresh permission dan explicit user consent. Tidak dari password, client_credentials, admin token paste, direct generic ORM create atau invented bootstrap endpoint.

- Opaque cryptographically random >=256-bit, base64url tanpa padding; token_digest=SHA-256(raw token), unique/indexed. Simpan raw hanya dalam successful response context sementara, bukan DB/log.
- Bind issuer/client/user/subject, approved scope/audience, token-session/family, client/user auth epochs dan trust identity.
- Initial family deadline = issue time +14 hari. Idle deadline = min(last successful rotation +24 jam, family deadline); pada awal last activity=initial issuance.
- Rotation tidak memperpanjang absolute family lifetime.

### FR-16 — Redeem dan rotation

- Require grant_type=refresh_token, raw refresh_token dan exact original-client authentication. Scope optional; issuer berdasarkan selected provider, bukan dari arbitrary JWT hint.
- Require row active, session active, now < idle deadline dan family deadline; recheck client/grant/user/binding/current policy/auth epochs.
- Absent scope -> prior granted scope; supplied scope subset prior grant dan current approved scope. Request tidak mengubah audience; audience parameter pada refresh ditolak. Policy removal tidak dipulihkan.
- Expired/revoked/wrong-client/unknown/consumed token -> invalid_grant tanpa detail enumeration.
- Success atomically consumes predecessor, creates one successor, emits fresh access jti/iat/exp dan raw replacement refresh. Refresh value tidak dikembalikan sama dengan predecessor.
- Unique parent-successor invariant dan concurrency control mencegah dua active successors. Consume/issue/storage tidak boleh partial jika signing gagal.
- Strict no-grace: retry old token setelah lost response tetap invalid; tidak hidupkan kembali token consumed. Known valid-client replay merevoke family/session dan successor secara persistent.
- Unknown/wrong-client token tidak menjadi arbitrary family-revocation primitive. Typed rejection response harus mempertahankan security-state writes, bukan rollback semua karena raised error.

### FR-17 — Session revocation dan access-token boundary

Model oidc.token.session mewakili user authorization family, bukan browser session. Simpan active/revoked, opaque sid, original client/issuer/user/subject, approved consent bounds dan absolute lifetime.

Revoke pada known code/refresh replay, admin explicit session revoke, user deactivation/password/auth-epoch security change, client disable/secret reset, atau identity/policy change yang membuat binding/grant tidak valid. Tidak memigrasikan azp/sub/client diam-diam.

Untuk **locally issued user access tokens**, self-provider decode memeriksa sid terhadap session active serta identity/auth epochs melalui internal service. Ini explicit enforcement yang membatalkan token session lokal, bukan asumsi bahwa revoke refresh otomatis membatalkan JWT.

External JWT yang diverifikasi stateless tidak memiliki jaminan immediate session revocation lokal. Machine access token mengikuti user/client/profile/key eligibility yang berlaku, tanpa mengklaim setiap secret reset universal langsung membatalkan semua machine JWT. Tidak ada public revocation endpoint baru pada release ini; restricted admin action cukup untuk session administration.

## 11. API dan transport contract

### FR-18 — Public model API

| API | Input/return |
| --- | --- |
| amr.oidc.helper.encode(issuer, scope=None, audience=None) | Access-only client_credentials acquisition; return nonempty access-token str |
| amr.oidc.helper.exchange(issuer, grant_type, code=None, redirect_uri=None, code_verifier=None, refresh_token=None, scope=None, audience=None) | Typed acquisition/exchange; return metadata-bearing dictionary; only accepted grant-specific fields allowed |
| amr.oidc.helper.decode(token) | Delegate full resource decode; verified claims, bukan signature-only dictionary |
| amr.resource.helper.decode(token) | Authoritative full resource verification/provenance |

exchange mendukung client_credentials, authorization_code dan refresh_token; code fields hanya code grant; refresh field hanya refresh grant; audience hanya initial issuance, bukan refresh. Password/user credentials/arbitrary claims tidak termasuk interface.

Public model acquisition tidak menerima raw caller client secret atau arbitrary client record ID. Selected trusted profile menentukan client_id dan protected credential reference. Caller harus trust administrator yang berwenang atau explicit service owner selected local client; non-admin caller tidak dapat memilih global profile orang lain. Protected server service melakukan actual client authentication; tidak menganggap env.su sebagai bukti authorization.

HTTP adapter mengekstrak client credentials lalu memakai private common exchange service dengan unforgeable server-owned auth context. Context internal tidak dapat dibentuk dari RPC dictionaries/user-supplied booleans. HTTP confidential-client auth adalah authority backchannel; tidak mewajibkan user browser session di /oidc/token.

encode tidak menerbitkan atau merotasi refresh lalu membuangnya; refresh/code callers memakai exchange. Model validation/access errors disanitasi; internal errors bertipe dipetakan ke HTTP tanpa token/secret/traceback.

### FR-19 — HTTP routes

| Route | Kontrak target |
| --- | --- |
| GET /oidc/authorize, /oidc/auth | Public entry, bind DB/provider, validate -> native login/consent; response_type code only |
| POST /oidc/authorize_continue | Authenticated completed user session, native CSRF=True; one-time approve/deny |
| POST /oidc/token | No browser session requirement; explicit confidential-client auth; form-urlencoded; three grants only |
| GET /.well-known/jwks.json | Public authorized verification keys only |
| /oidc/introspect | Preserve existing GET/POST URLs; authenticate confidential client; body token only, GET token query rejected; shared verified policy, no raw uid authority |
| GET /oidc/profile, /oidc/userinfo | Verified Bearer access token; resolved eligible bound user; no claim of OIDC userinfo compliance/ID token flow |
| GET /.well-known/openid-configuration | Remains 404; not auto-enabled |
| Existing login/continue UI routes | Safe same-origin UI only; /oidc/login/submit does not become password-token endpoint or bypass native login |

URL preservation does not preserve unsafe CSRF/redirect/credential behavior. Method restriction on authorization and protected consent POST, authenticated introspection, and query-token rejection are deliberate security deltas recorded here. Non-allowed methods return 405. Unknown/duplicate/forbidden grant parameters reject, not silently merge query and form.

Token success: JSON access_token:str, token_type='Bearer', expires_in:int, scope:str. Code/refresh additionally return refresh_token when authorized; code refresh absence only when client not permitted. Never id_token. no-store and Pragma:no-cache. Code/verifier and session internal metadata not in response.

| Failure | Response |
| --- | --- |
| Malformed/missing/repeated input, mixed credentials, forbidden overrides | 400 invalid_request |
| Client-auth failure via Basic | 401 invalid_client; WWW-Authenticate: Basic |
| Client-auth failure via body/no header | 400 invalid_client |
| Supported grant not allowed for client | 400 unauthorized_client |
| password/other unsupported grant | 400 unsupported_grant_type |
| Bad code/PKCE proof, invalid refresh | 400 invalid_grant |
| Unknown/expanded scope | 400 invalid_scope |
| Invalid initial audience | 400 invalid_request, generic description |
| Rate limit exhausted | 429 temporarily unavailable body with Retry-After, no credential details |
| Unexpected service failure | 500 sanitized server failure; never partial success |

Introspection invalid token with valid introspection client -> 200 {active:false}; invalid client -> client-auth error. Introspection active claims only after verification and allowed scope of client access; token client_id must match authenticated introspection client for this single-client profile. Profile failure -> sanitized 401; do not expose private/internal user fields by copying entire token payload.

Profile success release allowlist: sub, uid (resolved user ID), name (resolved display name), login (resolved login); no password/email/database/private code/session secrets. This stabilizes a minimal existing application profile endpoint, not ID-token semantics.

### FR-20 — Self-provider and external transport

- Local internal operations must produce zero **outbound self HTTP** across metadata/key/token/refresh helpers. Browser frontchannel login/authorization and incoming HTTP calls remain normal protocol interactions; zero-HTTP does not mean eliminate browser redirect flow.
- HTTP and internal service apply identical auth/grant/policy/provenance rules. Internal code redemption still needs existing consented code and correct verifier; no server-admin shortcut minting user refresh families.
- Shared validation selects one exact active trusted issuer before backend. Unverified hints never create trust; classification must not recursively invoke decode.
- External verification retains guarded supported transport. External acquisition exchange only uses configured protected endpoint/credential, with strict response shape validation and existing SSRF/TLS constraints. It does not claim external provider supports all grants.
- Local missing key/credential/session/binding -> reject, never HTTP/issuer/key/user fallback.
- Backend DB selected by deployment host/dbfilter/active server environment; request db/Host/claims cannot switch DB or canonical issuer.

## 12. Data and security administration requirements

Schema additions are design targets, not files already implemented:

| Model | Required data/invariants |
| --- | --- |
| oidc.provider | Singleton local provider, exact issuer, active, signer and allowed verification key relations, protected admin ACL |
| oidc.client | Unique OAuth ID/name, protected verifier hash, service user if required, explicit confidential/grant permissions/auth_epoch |
| oidc.client.redirect.uri | client_id FK, exact value; unique pair; approved HTTPS URI validation |
| oidc.client.audience / oidc.client.scope | Required per-client exact values/default markers and uniqueness |
| oidc.issuer.register.azp | Protected policy-child described in FR-06 |
| oidc.authorization.transaction | Opaque handle digest, browser/session binding, exact pending authorization values, expiry, single-use consent state |
| oidc.authorization.code | code_digest unique, issuer/client/user/subject/redirect/S256/scope/audience, epochs, issued/expires/consumed, derived session relation |
| oidc.token.session | Opaque unique sid/family, active/revoked, issuer/client/user/subject, consent bounds, auth epochs, absolute deadline |
| oidc.refresh.token | token_digest unique, session_id FK, parent_id unique for successor lineage, state active/consumed/revoked, issued/idle/family deadline, granted bounds |

All foreign-key client_id fields above point to oidc.client record IDs; OAuth string ID is a separate client property. Do not repeat source mismatch passing string to Many2one.

Provider administration group amr_oidc.group_provider_admin requires base.group_system; trust policy operations continue existing trust-admin guard. Ordinary internal users may read sanitized nonsecret client identity only as needed for consent, not secret/hash/code/session/refresh stores. Public/portal users have no generic CRUD on sensitive models. Native authorization UI uses server service with narrow privilege and explicit transaction binding, not broad read access to token stores.

Client secret verifier uses approved salted password-hashing facility compatible with Odoo 13 target; constant-time verification. Outgoing protected credential reference is separate reversible server secret, not confused with verifier hash. Never expose either through read/export/debug logs.

No raw access/code/verifier/refresh/client secret/user password in logs, exception messages, analytics or cron evidence. Audit sanitized IDs, event/reason/time and actor; do not store raw external callback/state as audit content. Token-store cleanup must retain consumed/revoked family evidence until absolute family deadline plus 24 hours; cleanup is not validity enforcement. Authorization transaction/code cleanup retains minimal replay linkage for issued-session lifetime, without raw code values.

## 13. Nonfunctional requirements

### NFR-01 — Concurrency/transactions

Atomic code use and refresh rotation, stable lock ordering, unique constraints and persisted replay revocation mandatory. Exact transaction strategy must respect Odoo ORM and project SQL restrictions. If ORM cannot meet invariant, Developer raises explicit technical exception for Lead rather than adding raw SQL/monkey patch silently. This is implementation review work, not unresolved product scope.

### NFR-02 — Authentication abuse limits

Accepted D2 values:

- Rolling 5 minutes: at most 10 failed client-auth attempts per exact client identifier.
- Rolling 5 minutes: at most 5 failed user-auth attempts per client+exact-login, if provider initiates native login context; no separate user-password token endpoint exists.
- Rolling 5 minutes: at most 60 failed auth/proof attempts per trusted source IP across identifiers.

The threshold-reaching failed attempt is rejected normally; further attempts before the rolling count falls below threshold receive 429/Retry-After. Counters shared/persistent across workers; unknown-client/user identifiers handled without enumeration. Native login's stricter auth/MFA/lockout policy is never weakened. Missing trusted proxy configuration cannot make arbitrary X-Forwarded-For authoritative. Internal callers require client/caller counters; absence of network IP does not bypass all limits.

### NFR-03 — Transport/browser security

External protocol HTTPS, production cookies Secure/HttpOnly with framework-compatible SameSite protection; native CSRF on consent; no open redirects, downgrade PKCE, third-party consent resources or credentials in URI. Token endpoint form limits: at most 16 KiB body; code/verifier/refresh raw lengths bounded to documented formats (verifier 128, opaque code/refresh 43 base64url chars for 32 random bytes). Client/state/URL/scope configuration bounded at 1024/1024/2048/4096 chars respectively; oversize reject before expensive work. These are release design limits, not RFC-mandated universal maxima.

### NFR-04 — Portability/observability

Odoo 13/Python 3.7 target, OCA/framework conventions, no production-code generation in PRD. Product docs portable under addon README/docs, task evidence under docs/ADDONS13-48. Log reason/status/IDs without credentials; monitor auth failures, rate limits, issuance, code reuse, refresh reuse/revocation and rejected policy revisions.

## 14. User journeys

1. Administrator fresh-install resource/provider, configure keys/local issuer, one trusted issuer profile/client ID, exact audience/azp and bindings; no activation with incomplete required policy.
2. Machine backend requests client_credentials through encode/exchange or token endpoint, authenticates client, obtains access token mapped to eligible service account; no refresh token.
3. User application creates random state/verifier, S256 challenge and starts browser authorization. Server uses native completed login/MFA, shows consent, then issues one code to exact redirect.
4. Application backend verifies state/iss, redeems code with client auth+verifier, gets access token and authorized initial refresh. Identity is consented user, not machine client owner.
5. Application uses access token against resource; local adapter verifies signature/policy/session and resolver provenance. Application refreshes using current token, atomically replaces both response values.
6. On reuse/revocation/expiry, application reauthorizes through code+PKCE; it never falls back to password grant or reuses consumed refresh.

## 15. Acceptance criteria PRD

Ini kriteria hasil produk, **bukan dokumen UAT atau klaim eksekusi**.

| AC | Hasil wajib |
| --- | --- |
| AC01 | Fresh resource-only dan provider+resource composition tidak membutuhkan functional amr_token; asset/import/dependency ownership konsisten |
| AC02 | encode -> string; exchange -> metadata; decode -> verified resource provenance; no duplicate wrappers/recursive original method chain |
| AC03 | Hanya client_credentials,authorization_code,refresh_token supported; password dan implicit ditolak tanpa config opt-in |
| AC04 | Client_credentials valid menghasilkan RS256 at+jwt token dan correct service binding, tanpa refresh/id_token |
| AC05 | Authorization membutuhkan exact registered redirect, S256/state, complete native login/MFA dan bound CSRF-protected explicit consent |
| AC06 | Initial refresh hanya berasal dari successfully redeemed consented authorization code; tidak ada password/bootstrap/admin bypass |
| AC07 | Code/verifier/client/redirect/issuer/principal bindings dan TTL/single-use berlaku; no double issuance pada concurrency |
| AC08 | Refresh opaque/digest-only, client/user/issuer/scope/audience bound, 14-day absolute/24-hour idle, single-use rotation dan no privilege expansion |
| AC09 | Proven replay persists family/session revocation walau error response; wrong-client/random input tidak dapat revoke arbitrary sessions |
| AC10 | Local user-token sid enforcement menolak revoked session; external/stateless revocation limitations tidak disamarkan |
| AC11 | Self-provider scoped operations tanpa outbound self HTTP, dengan parity auth/policy checks dan no silent fallback |
| AC12 | azp exact name global unique archived-inclusive, URL no fragment, child ANY matching; independent single-client/audience checks tetap |
| AC13 | Child direct CRUD/reparent/snapshot/revision/concurrency menjaga valid policy dan menginvalidasi stale provenance |
| AC14 | Secret/code/verifier/refresh data tidak readable via ordinary/public/portal ORM/RPC/export/log; privilege sempit terdokumentasi |
| AC15 | Grant error/status/headers, URL ownership, safe callback and introspection/profile contracts mengikuti PRD; no duplicate route publication |
| AC16 | Access TTL/expiry boundary, signer selection, auth epoch/eligibility dan supported algorithm fail closed |
| AC17 | Shared rate limits, bounded parsing, CSRF/PKCE downgrade prevention dan no open redirect berlaku pada real integration |
| AC18 | Fresh-only limitation, supported confidential-client profile, API/endpoint changes dan excluded OIDC capabilities terdokumentasi; tidak ada upgrade-ready claim |

Acceptance perlu evidence dari actual implementation pada gate berikutnya. Sesi ini tidak menjalankan test atau membuat UAT. Perintah test/runtime tidak dikarang; penetapan runner dan evidence merupakan pekerjaan Developer/Tester setelah authorization/gates yang berlaku.

## 16. Implementation impact dan urutan handoff

| Area/file | Perubahan target |
| --- | --- |
| amr_oidc/__manifest__.py, models/__init__.py, controllers/__init__.py | Direct dependency, model registration dan moved assets; hapus runtime parent-addon imports |
| amr_oidc/models/helper.py; proposed token_engine.py/resource_helper.py | amr.oidc.helper, typed exchange, local backend seam/private engine |
| amr_oidc/models/oidc_client.py; proposed provider/redirect/audience/scope models | Client/key/profile/grant configuration, secret protection dan exact registrations |
| amr_oidc/models/oidc_authorization_code.py; proposed authorization_transaction.py | PKCE, consent transaction, hashed code, one-use redemption/session linkage |
| amr_oidc/models/oidc_refresh_token.py; proposed token_session.py | Opaque digest store, session binding, rotation, revocation and replay |
| amr_oidc/controllers/main.py; login/consent templates | Safe native login integration, consent CSRF, token/route serialization |
| amr_token/models/public_key.py -> amr_oidc/models/public_key.py | Ownership transfer, selected signer/key loader; model identity tetap amr.public.key |
| amr_resource/models/helper.py, res_users.py, ir_http.py | Canonical decode/callers, strict provenance and provider-neutral base |
| amr_resource/models/trust_registry.py, views/security | Child azp, protected policy state/revision/snapshot |
| Moved settings/menu/ACL/tests/docs and consumer callsites | Fresh composition, security groups, registration, wrappers, product documentation |

Developer tidak sekadar copy dua class TokenHelper ke satu file sehingga definition saling overwrite. Pisahkan base engine/service dan extensions; module load order eksplisit. Compatibility ledger memuat model/method/signature/return/caller/alias disposition. Fresh install tidak membutuhkan installed-DB XML-ID migration, tetapi semua new manifest/XML references harus valid.

Urutan setelah review PRD: Lead menerima Step 0 sesuai workflow -> authorized Coding/unit tests -> unified Code Review (general/security/Semgrep) -> UAT setelah dokumennya dibuat/diterima -> Owner review/PR acceptance. PRD ini tidak mengotorisasi menjalankan urutan tersebut atau menandai acceptance. Deployment tetap Owner CI/CD di luar manual gates.

## 17. Risiko, trade-offs dan readiness

- Scope bertambah nyata dari controller move menjadi full code+PKCE user authorization. Existing helper names/bodies tidak membuktikan capability siap.
- Confidential-only/HTTPS-redirect restriction memperkecil surface release; public/native clients memerlukan scope/kontrak terpisah, bukan menerima browser-stored client secret.
- Single-client_id issuer profile tetap membatasi multiple app clients pada issuer global yang sama; accepted limitation, bukan bug yang diatasi dengan melemahkan verifier.
- Strict rotation membuat response-loss/concurrent-refresh memerlukan reauthorization; client wajib serialisasi refresh dan store replacement atomik.
- Local user-session checks menambah database read path, tetapi memberi explicit revocation enforcement tanpa self HTTP. Jangan cache yang melewati revocation/epoch checks.
- Privileged key/secret stores dan existing broad ACL memerlukan review security aktual; no-secret-read bukan cukup UI password mask.
- Resource scope stub tidak memberi granular authorization; existing ACL/record-rule dan explicit consent/bindings tetap wajib. Scope/RBAC engine baru tidak diklaim.
- Existing DB/token compatibility tidak didukung. Jangan menguji fresh-only dengan menghapus data existing atau uninstall tanpa authority.
- Lead perlu rekonsiliasi sibling task/baseline/source ownership (provider/resource/consumer) tanpa mengubah keputusan task ADDONS13-48 atau menggandakan issue tahap.
- Open product clarification: **tidak ada setelah jawaban authorization_code+PKCE**. Readiness teknis masih belum dibuktikan: main freshness, runtime Odoo/Python/library, actual registry/routes/ACL, approved transaction mechanism, dan integration evidence.
- Status akhir: PRD DRAFT, Lead acceptance PENDING; implementation/test NOT RUN; dokumen UAT belum dibuat sesuai permintaan Owner.

## 18. Sumber

### Keputusan dan source proyek

- Pesan Owner dalam percakapan: koreksi task, penerimaan K/C/D, fresh-only, pembatalan password dan jawaban klarifikasi “Tambahkan authorization_code + PKCE sebagai sumber refresh token awal.”
- Source references S01–S14 pada bagian 5; merupakan pembacaan file working tree, bukan klaim commit-bound runtime behavior.
- AGENTS.md:7–18,76–105: target framework/ORM/security/testing dan lokasi PRD task.
- /home/ubuntu/docs/standards/DEVELOPMENT-WORKFLOW.md:29–43,52–76,124–143: Step 0/acceptance, empat gate dan product/task documentation.

### Standar eksternal yang diambil/dibaca

- [RFC6749 §2.3.1, §4.1, §4.4, §5, §6](https://www.rfc-editor.org/rfc/rfc6749.txt): confidential client authentication, authorization code/client credentials/token responses, refresh client/scope binding. Request password tidak lagi diimplementasikan.
- [RFC7636 §4.1–4.6](https://www.rfc-editor.org/rfc/rfc7636.txt): verifier grammar, S256 transformation, authorization challenge binding dan token endpoint verification. Release ini memilih S256-only, tidak plain fallback.
- [RFC9700 §2.1.1, §2.4, §4.1, §4.8, §4.14](https://www.rfc-editor.org/rfc/rfc9700.txt): modern PKCE/security guidance, password MUST NOT, exact redirect dan anti-downgrade/refresh replay guidance. Pembatalan password mengikuti keputusan Owner, bukan risk waiver.
- [RFC9068 §2, §4](https://www.rfc-editor.org/rfc/rfc9068.txt): access-token typing/claims/verification; actual supported resource profile masih mengikuti batas source dan PRD, bukan klaim complete interoperability certification.
- [OpenID Connect Core §2](https://openid.net/specs/openid-connect-core-1_0.html#IDToken): azp ID Token mempunyai semantik Client ID; application azp=name di PRD ini tidak diekspor menjadi ID Token nonstandard.

Retrieval memakai web_extract dan cached source-text reads pada rangkaian analisis. Automated citation-ledger execution tidak dijalankan. Tidak ada UAT document, code implementation, test execution atau runtime compliance result yang dihasilkan oleh PRD ini.

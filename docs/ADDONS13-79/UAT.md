# UAT — ADDONS13-79

**DRAFT FINAL — menunggu persetujuan Owner.** Dokumen ini adalah konsolidasi publik tersanitasi, bukan artefak asli yang disetujui berdasarkan hash, bukan rebind kandidat, persetujuan konfigurasi, waiver, atau hasil UAT. Setiap kasus di bawah adalah rencana baru dengan **actual NOT RUN**; status tersebut tidak mengubah atau menyatakan hasil catatan eksekusi yang pernah ada.

## Prasyarat bersama dan cara pembuktian

- Sebelum eksekusi: persetujuan PRD/UAT dan binding kandidat yang tepat, otorisasi terpisah untuk test, runtime dan DB, serta konfigurasi final disetujui untuk Odoo 13 / CPython **3.7.3**, image immutable/digest, source snapshot, dependency closure, selector dan command, batas run, network, resource limits, tempat evidence dan cleanup/readback. SCOPE-01 tetap OPEN sampai ada disposisi. Kekurangan prasyarat berarti **BLOCKED; actual NOT RUN**, bukan PASS.
- Kriteria fresh mapping dan profil positif tetap dipertahankan, tetapi keputusan scope Owner terpisah untuk pembuatan mapping issuer fresh-only dan profil RS-compatible terkait masih PENDING verifikasi, tidak otomatis dipenuhi oleh acceptance spesifikasi. Sampai gate terpenuhi, uji issuance positif terkait BLOCKED; actual NOT RUN. Kasus independen yang berlaku tidak dihapus, dan hasil parsial bukan penerimaan keseluruhan fitur.
- Fixture default: database fresh sekali pakai yang kepemilikan/ketiadaannya diverifikasi; komposisi addon sesuai kasus, synthetic issuer, client, user, company, credential dan RSA key; trust dan binding eksplisit, jam terkendali, signer/cache/transport observer, serta baseline legacy terpisah bila kasus memerlukannya. Public, portal, internal, system admin, trust admin, service issuer dan actor berbeda disiapkan sesuai skenario. Operasi dilakukan Tester yang diotorisasi, dengan admin dan security/deployment owner untuk tindakan khusus. Semua varian dijalankan masing-masing; tidak satu hasil substitusi bagi varian lain.
- Untuk setiap kasus: rekam kandidat dan identitas snapshot/diff, komposisi/urutan, actor, konfigurasi/provenance, fixture dan command/selector, versi interpreter/dependency terukur, expected, actual, status dan bukti tersanitasi. Sertakan assert sebelum signer/cache/network, pembacaan balik registry/DB/ACL dan observasi langkah di mana diminta; bukti hanya ringkasan, hitungan, lokasi aman dan screenshot tersanitasi bila relevan. Jangan menyimpan token bearer, kunci privat, credential, data pribadi atau payload rahasia.
- Instrumentasi zero self-provider HTTP harus mengamati seluruh operasi validasi lokal termasuk klasifikasi, pemilihan key dan error melalui HTTP client/transport dan egress process/socket. Buktikan observer dengan kontrol positif yang diotorisasi secara terpisah; traffic unrelated, frontchannel normal dan remote tidak dilarang. Mock saja tidak membuktikan network oracle, ACL atau registry nyata.
- Segera setelah run, hapus hanya resource run-owned yang tercatat, termasuk pada kegagalan, dan verifikasi ketiadaan setiap ID secara independen. Catat kegagalan/ketidakpastian cleanup terpisah dari verdict fungsional.
- Kasus legacy tidak mewarisi default/override fresh; pembatasan yang mengubah kontrak legacy memerlukan persetujuan terpisah. Kasus rotasi normal dan kompromi dibedakan. Bila fixture lifecycle, migrasi, replay, kontrak error atau konfigurasi belum disetujui, bagian terkait tetap BLOCKED. Test desain atau inspeksi statis bukan bukti eksekusi.

## Kasus rinci

Setiap kasus memakai fixture, actor dan bukti bersama di atas, ditambah varian eksplisit di langkahnya. Semua persyaratan dalam satu kasus adalah assertion yang harus dibuktikan; setiap hasil aktual awal **NOT RUN**.

### D01-COMP-01

**Fixture, tindakan dan expected:** On an isolated fresh Odoo13/Python3.7.3 DB, install `amr_oidc` without `amr_resource` or `amr_oidc_resource`; then install `amr_resource` without provider/glue. Verify each base registry loads and manifests have no cross-base dependency.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### D01-COMP-02

**Fixture, tindakan dan expected:** Verify glue remains opt-in (`auto_install=False`); separately install `amr_oidc_resource` over both bases. Verify dependency resolution and registry load. Repeat supported install orders in fresh disposable DBs; record exact order and result.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### D01-COMP-03

**Fixture, tindakan dan expected:** With glue installed, invoke provider glue `get_access_token` under its allowed actor and inspect synthetic token claims: prove call follows legacy `_generate_user_token` contract and characterize its actual claims/verification outcome. Do NOT label this fresh-profile issuance or infer RS-compatible fresh claims.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### D01-COMP-04

**Fixture, tindakan dan expected:** Separately call authenticated `/oidc/token` client_credentials flow through the registered route with synthetic client credentials; verify fresh issuer subject and required claims, then submit to the actual RS verifier with the prescribed configured audience/issuer/key. Assert both the issuance and verification contracts independently.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### D01-COMP-05

**Fixture, tindakan dan expected:** Exercise RS-owned methods with `amr_resource` alone and with glue composition; prove no provider requirement or altered RS API.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### D01-COMP-06

**Fixture, tindakan dan expected:** In provider glue, exercise `create_access_token`, `add_url_access_token`, and `get_auto_login_url`; preserve accepted denial/no default URL bearer behavior. Also verify the moved five methods have one intended provider owner, not duplicate provider definitions.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### SCOPE-01

**Fixture, tindakan dan expected:** Lead membandingkan seluruh path perubahan kumulatif terhadap scope fitur yang disetujui, termasuk root, harness, dokumen dan sibling. Lampirkan disposisi Owner yang eksplisit pada setiap pengecualian: terima dengan alasan, pisahkan, atau hapus dengan otorisasi tersendiri. Rekonsiliasi deskripsi scope yang berbeda dengan diff tepat; tanpa seluruh disposisi, OPEN dan tidak ada PR.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### C01

**Fixture, tindakan dan expected:** Explicit fresh provenance, key absent: scoped issuance reads 900 seconds; Settings may display 900 but read/issue does not create key. Refresh helper retains its baseline missing-key result 86400; refresh creation remains source 14 days. Verify signed exp minus iat and response TTL equal 900.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### C02

**Fixture, tindakan dan expected:** Fresh profile explicitly save 60 then 86400 as authorized settings actor: scoped issuance uses exact values; shared refresh reader sees the stored same value, no claim its creation lifetime changed. UI discloses coupling before save; no other setting or silent write.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### C03

**Fixture, tindakan dan expected:** Existing and unknown provenance, separately stored absent, 3600, 86400, 59, malformed: no key write, no new-profile issuance and no conversion. Characterize legacy issuer/helper and refresh behavior against baseline fixture for each, including exceptions and `expires_in` falsy/override semantics; compare exact outcome, not assumed validity. Existing other token classes/claims unchanged except independently accepted #79 modifications.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### C04

**Fixture, tindakan dan expected:** Fresh scope parameter tampered with empty, whitespace, signed, decimal, non-ASCII digits, zero, 59, 86401, huge or text: sanitized `UserError` for invalid configuration before signer and cached return; unauthorized actor receives `AccessError`; protocol boundary maps errors to its existing sanitized protocol error without secrets. Authorized settings write rejects invalid. Check 60/86400 controls. Ordinary actor cannot change setting through UI or direct RPC; privileged direct tamper cannot bypass issuance validation. Record effective ACLs.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### C05

**Fixture, tindakan dan expected:** Fresh scope override omitted, int 60, configured TTL pass; None, bool, 0, 59, >configured, 86401, float/string reject before signing. No restrictions imposed on legacy helper args by this delta.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### C06

**Fixture, tindakan dan expected:** Instrument signer and controlled clock; two scoped calls each revalidate auth/config and mint, no scoped cache return. After a worker observes config B its next issuance uses B; concurrent reads measured without inventing global propagation. Existing tokens retain signed exp and verifier rejects at configured boundary, subject to policy/trust. Required legacy cache cases still apply.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M01

**Fixture, tindakan dan expected:** Approved fresh mapping, same issuer and user two issuances and after login/email rename: same exact 64 lowercase-hex opaque subject, no uid/login/db claims; different user differs. No caller-selected subject accepted; inspect actual payload only in secured synthetic fixture.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M02

**Fixture, tindakan dan expected:** Verify generation uses Python standard-library `secrets` for 32 bytes, Odoo SQL uniqueness constraints and no raw SQL. Concurrent first issuance for same pair yields exactly one persisted row/same subject; observe savepoint handling and exact `(namespace, principal)` reread after integrity conflict. Independently force deterministic subject collision in isolated test seam: retry then success; repeated collision beyond three attempts denies, no partial issuance. DB rejects duplicate namespace/principal and namespace/sub including archived rows.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M03

**Fixture, tindakan dan expected:** Attempt write/reassignment, reparent, namespace/subject edit, unlink and deletion of referenced user, including privileged model RPC; reject, retain reservation. Archived mapping cannot issue and cannot be reused. Missing/ambiguous namespace and inactive/deleted principal fail before signing.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M04

**Fixture, tindakan dan expected:** Different explicitly configured fresh DB/issuer namespaces isolate mappings; cloned/restored DB, missing/changed namespace or reused namespace absent separate authorized lifecycle plan: scoped issuance blocked; no rewriting identity. Treat cross-instance uniqueness as operational evidence, not inferred from DB constraint.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M05

**Fixture, tindakan dan expected:** Public, portal, regular internal, system administrator, trust administrator, legitimate issuance service: attempt mapping read/search/create/write/unlink and exposed RPC, plus forged context/sudo kwargs. Only private service path after actor/client authorization can read/create; no human bypass of immutability. Prove actual ACL/record-rule and sudo boundaries with installed registry, not view inspection.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M06

**Fixture, tindakan dan expected:** Valid authenticated active registered client A issues; signed client_id A; correct explicitly bound issuer/user/audience RS trust verifies. Missing/forged auth provenance, request kwargs client B, inactive/unknown/ambiguous client, mismatch issuer/audience, unauthorized user or direct glue without authenticated client all fail before signer; unrelated legacy path unchanged.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M07

**Fixture, tindakan dan expected:** Tamper each signed header, payload, signature; wrong algorithm/type/key/kid, untrusted/expired key, missing/wrong iss/aud/iat/exp/jti/client/azp, expiration, invalid policy and provenance: RS rejects without fallback. Include valid cryptographic positive control and independently configured local PEM vs JWKS key selection; never weaken existing verifier.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M08

**Fixture, tindakan dan expected:** Explicit RS binding maps verified issuer/sub to intended eligible user: pass. Missing, wrong-user, inactive, ambiguous or forged/unverified subject: deny, no email/login fallback, automatic binding or rewrite; malicious RPC cannot create binding absent existing trust-admin privilege. Assert no self-provider HTTP on success/classification/key/error paths; remote parity retained.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### M09

**Fixture, tindakan dan expected:** Legacy login-sub tokens and RS bindings in existing fixture: no conversion, alias or new dual acceptance, legacy profile remains unchanged where not explicitly changed by accepted #79. No claim other feature acceptance; sibling owners review captured contract evidence.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### R01

**Fixture, tindakan dan expected:** Compromised synthetic K: remove from every configured JWKS/local PEM and other actual verifier trust, test old signed and newly forged unexpired K token rejects only after verified propagation to each worker/region. Stale verifier negative control prevents containment claim; if removal cannot be verified fail affected path closed. Replacement R passes only after trusted.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### R02

**Fixture, tindakan dan expected:** Security owner supplies threat/replay/legacy/clone exposure review, verifier inventory, named incident owner, measurable propagation and redacted evidence. Deployment owner supplies separate inventory/rollback before rollout proposal. Any remaining risk remains OPEN absent explicit Owner disposition; evidence is not a waiver.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### G01

**Fixture, tindakan dan expected:** Verify separately accepted dependency separation and both install orders, five provider moves/glue-only API, RS independence, URL denial and applicable V/U cases; do not declare #79 accepted if any required test blocked. No sibling feature is silently modified.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### T01

**Fixture, tindakan dan expected:** Fixture fresh terverifikasi, key TTL tidak ada; jalankan issuance fresh yang terautentikasi melalui setiap entry point fresh yang diizinkan. Assert TTL 900, signed exp−iat dan metadata respons sama; Settings memakai satu key dan menampilkan detik tanpa menulis. Simpan 60 dan 86400 sebagai actor berwenang dan pastikan masing-masing dipakai. Jangan menerapkan TTL fresh pada jalur legacy glue; karakterisasi jalur itu secara terpisah.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### T02

**Fixture, tindakan dan expected:** Known existing DB fixture with stored 3600 then 86400: before any separately approved migration prove no overwrite/reinterpretation, including refreshing Settings. With approved rollout verify exact value preserved. Existing missing or unknown deployment provenance must not default to 900 or silently write it; new contract issuance blocks pending explicit migration choice.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### T03

**Fixture, tindakan dan expected:** Fresh profile: Settings writes and direct parameter tampering with empty, spaces, ` 60`, `60 `, `+60`, `-1`, `0`, `59`, `86401`, `60.0`, non-ASCII digits, text, huge integer: UI rejects save; config-read/issuance returns sanitized configuration error before signer and before any warm cache return; no fallback/clamp. Integer endpoints 60/86400 remain positive controls.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### T04

**Fixture, tindakan dan expected:** Fixture fresh dengan TTL valid dan signer/cache spy: uji omission, integer 60 dan TTL efektif sebagai kontrol positif; uji None eksplisit, bool, nol, negatif, pecahan, string, kurang dari 60, melebihi 86400 atau TTL efektif. Setiap input invalid ditolak sebelum signer/cache pada semua entry point fresh berwenang termasuk RPC bypass. Jangan menerapkan pembatasan baru pada API/helper legacy; perubahan kontrak legacy memerlukan persetujuan kompatibilitas terpisah.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### T05

**Fixture, tindakan dan expected:** Controlled clock, prior valid token and cache: sign with configured A, change to B, reissue after each worker observes change; signed exp and returned metadata reflect effective B and no token from A is returned. Previously signed token keeps exp but may fail policy/trust; at/after exp verifier rejects with source baseline leeway=0. Warm cache cannot return expired token or bypass auth/config checks; test DB, audience, actor, key and policy isolation and concurrent changes. Record real propagation; no promised instantaneous cross-worker effect.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### T06

**Fixture, tindakan dan expected:** Inventory shared-key readers/extensions, preserve refresh helper behavior and 14-day source issuance implementation; in separately approved migration fixture verify old values, fresh/missing and rollback and record observed effects on refresh reader, without changing refresh feature. If a key change would affect a refresh consumer and no compatible plan is approved, rollout is BLOCKED, not PASS.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### I01

**Fixture, tindakan dan expected:** Approved issuer mapping fixture: issue twice for one principal/issuer/database, then rename login/email and reissue; exact same nonempty opaque sub; two principals under same issuer differ. No subject equals login/email or exposed raw DB id; verify scoped profile omits uid/login/db identifying claims. Keep evidence synthetic.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### I02

**Fixture, tindakan dan expected:** Simultaneous issuance for same `(issuer_namespace, principal)` yields one persistent mapping and same sub; attempt second mapping for same pair rejected by DB uniqueness. Same issuer + same sub mapped to another principal is rejected by DB uniqueness; different issuer/DB isolation verified with separately established namespaces. Unknown/ambiguous/reassigned/deleted identity rejects; no silent mapping reuse. Test clone/issuer changes only with separately approved lifecycle.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### I03

**Fixture, tindakan dan expected:** With authenticated active registered client A issue scoped token: signed client_id exactly A's record, RS validates under matching profile. Forged claim or kw client_id B, audience substitution, missing auth, inactive/unknown client, auth for B presented as A, and ambiguous mapping all reject before signing; direct glue/helper without authenticated client cannot issue this RS profile. Independent legacy non-RS operation is assessed separately.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### I04

**Fixture, tindakan dan expected:** Existing login-sub token, legacy client and RS subject binding fixtures: inventory affected accepted consumers; no automatic rewrite, alias, replacement or altered claims outside approved profile. If no Owner/sibling-approved compatibility and issuer-model scope, mark positive issuance blocked. Baseline RS-side `(issuer, sub)` binding alone must not be asserted as issuer-side `(issuer, principal)` uniqueness.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### K01

**Fixture, tindakan dan expected:** Trust-admin-controlled synthetic key K signs valid unexpired token; every explicitly configured verifier initially accepts under otherwise valid profile. Simulate compromise; disable signing, remove K from JWKS and independently configured local PEM trust, invalidate/refresh permitted caches and distribute distinct replacement key R. During propagation record actual acceptance/rejection and last verifier; no claim of immediate rejection.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### K02

**Fixture, tindakan dan expected:** After evidence confirms propagation to **each** verifier/worker/region and no K trust/fallback remains, previously issued K token and newly forged unexpired K token both reject; R-signed otherwise valid token passes only once explicitly trusted. Include stale cache/verifier still trusting K as negative control: propagation is incomplete and containment cannot be claimed; if cannot clear, affected path/profile fails closed.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### K03

**Fixture, tindakan dan expected:** Verify incident record includes affected issuers, detection, trust removal, distribution, last-verifier time and exposure communications without credentials. Normal planned overlap tested separately; compromised K never retained by intentional overlap. No per-token revocation or universal exposure deadline asserted.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V01

**Fixture, tindakan dan expected:** Fresh provider-only: five provider declarations absent from provider; no glue selected; independent provider `_generate_user_token`→`decode` succeeds for explicitly configured synthetic fixture and malformed/missing configuration fails. Verify provider declaration of `get_access_token` is glue-only; record effective public method status and legacy impact without assuming core/third-party absence or a particular exception.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V02

**Fixture, tindakan dan expected:** RS-only: all five existing RS declarations retained, actual signatures and policy verified, direct issuance fails, URL wrappers pass through. Exercise separately configured synthetic RS verifier positive/negative, no provider/glue in closure.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V03

**Fixture, tindakan dan expected:** Both bases no glue in both fresh install orders: provider independent helper operation; RS independent positive and unknown issuer negative; compare registry/MRO, signatures, actual method dispatch and default nonsecret trust snapshots, no glue, issuer, fallback/discovery or trust introduced. Lead and sibling owners review whether this fixture establishes the applicable accepted sibling oracle; do not demand an unaccepted public-method fixture or assert sibling pass here.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V04

**Fixture, tindakan dan expected:** Glue explicitly installed in both orders, `auto_install=False`, no cyclic/base-to-glue dependency; verify moved five plus private helper/sentinel owner, retained RS source declarations and actual effective MRO, no implicit trust and no accidental activation. Dependency failure tested only using authorized isolated fixture.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V05

**Fixture, tindakan dan expected:** Login template on provider-only, RS+provider in both no-glue orders, glue: proposed provider-specific UI hook has baseline `True`, without `super`, context flags or registry sniffing; true/false override shows/hides Continue; public and authenticated user rendering stays controlled; no call to moved policy, glue, signer or token; verify no issuance. Exercise direct authorize/continue and submit routes: remain unsupported. Document old override/custom addon impact.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V06

**Fixture, tindakan dan expected:** Both RS GET routes in RS-only, both no-glue orders and glue, supported `auto_login`/`access_token`, URL branch, malformed type, absent URL, internal/public model paths, model `get_url_access_token` direct-result branch and auth failures; compare actual status/shape/Location/headers with approved contract. The proposed RS-owned route helper/pass-through and its no-token-regardless-of-MRO oracle require contract review/approval; pending that decision, the helper-specific assertion is BLOCKED, actual NOT RUN. If approved, instrument helper/signer to verify the proposed oracle without assuming model branch safety. Obtain independent security review of generic redirect/open-redirect and model-generated URL risks, not a blanket safety claim.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V07

**Fixture, tindakan dan expected:** Glue direct access: self vs ordinary different actor vs system, singleton/empty/multiple, policy false, inactive/unauthorized where contract says; denied before cache and signing, even warm hit, across RPC/machine/public/portal and forged context. Test persistent `create_access_token` explicit controlled denial with no storage/signature.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V08

**Fixture, tindakan dan expected:** Glue omission sentinel survives defaults/wrappers/cache/private boundary; omitted argument causes helper call with no audience argument, explicit None rejects; empty/malformed vs valid string/list, list tuple roundtrip, resource precedence and invalid resource rejection. No sentinel identity substitution from token_helper.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V09

**Fixture, tindakan dan expected:** Cache: same/different uid and normalized audiences, bucket rollover, actual expiry, policy/key/user/company/revision changes and explicit invalidation including concurrent changes, DB isolation; a stale/unauthorized hit never mints/returns a usable token. Expectations need approved lifecycle; verify no cross-context leakage.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V10

**Fixture, tindakan dan expected:** Glue direct URL helpers and RPC: default must issue no bearer into URLs; proposed controlled denial with no signer/cache use and sanitized failure for all types, including auto-login and explicit audience/resource, is pending exact contract approval. If Owner separately approves an exception, specify reviewed origin/redirect, audience, caller, expiry/replay and leak-control cases; do not infer approval. No bearer in evidence.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V11

**Fixture, tindakan dan expected:** Delete mobile method in controlled first-party closure provider-only, RS-only, both orders, glue, legacy adapter: first-party declaration removal and no alias/shim; record effective registry resolution and direct/RPC result without assuming absence in Odoo core or third-party addons or any particular exception. Audit external/dynamic consumers separately.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V12

**Fixture, tindakan dan expected:** Move relevant registered provider integration tests and source-loaded standalone/security fixtures to correct glue target; preserve all applicable actor, audience, cache, rejection and security assertions; independently run remaining provider issuer tests and reconcile applicable `amr_token` legacy loader/alias coverage. No silently dropped cases.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V13

**Fixture, tindakan dan expected:** Explicit local trusted binding off by default; wrong/missing/ambiguous provider, DB, issuer, client, kid, key, algorithm, token class, signature, claims, timing, audience, azp, stale policy/provenance, wrong company/user all reject. Approved valid provider access token passes same RS verifier. No ID token or generic JWT; no weakening, implicit trust or fallback.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V14

**Fixture, tindakan dan expected:** Exercise actual merged-registry classification/backend path with no classification mock; backend selected once with bounded call count; verify the bounded internal interface receives explicit identity/arguments and does not consume bearer or Basic from ambient request, including when ambient headers differ; local errors fail closed, zero introspection/self-provider HTTP including key/metadata/failure; calibrated transport instrumentation. Remote branch independently retains approved security and transport.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V15

**Fixture, tindakan dan expected:** Pada Odoo 13 dan CPython 3.7.3 yang disetujui, dengan dependency terkwalifikasi dan database fresh terisolasi yang diotorisasi, periksa import, route, ACL, registry, urutan addon dan seluruh hasil test yang berlaku. Catat runtime aktual dan cleanup/readback; jangan mengekstrapolasi ke upgrade atau addon pihak ketiga.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V16

**Fixture, tindakan dan expected:** Review release and cross-issue impact: explicitly list five public API compatibility changes, deletion and external unknowns; preserve applicable sibling requirements and clarify that the proposed fixture is not accepted. Owner decisions, security risk and hash approval separately recorded; no waiver inferred.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U01

**Fixture, tindakan dan expected:** Fresh provider only and RS only: each starts, imports and works in its own existing bounded capability without the other/integration; no implicit trust. Verify actual installed closures.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U02

**Fixture, tindakan dan expected:** Fresh both install orders without integration: both load; no new trusted profile/key or local acceptance. Record closure, effective registry/method ownership, ACL and configuration.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U03

**Fixture, tindakan dan expected:** With chosen integration installed but disabled: baseline unaffected, no new trust; remove/disable backend while enabled => fail closed, no silent HTTP/introspection. Include provider-only, RS-only and optional amr_token legacy adapter if supported.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U04

**Fixture, tindakan dan expected:** Positive: approved local issuer uses real selected issuance path with approved authenticated user/client and real synthetic RS256 key. Confirm actual header and required claims, valid exact RS policy, resolver/binding, eligible user; verify RS returns accepted verified provenance and correct user. Not a handcrafted token standing in for issuer.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U05

**Fixture, tindakan dan expected:** Signature tamper, different key, wrong kty, RSA <2048, none/HS256/other alg, invalid key, malformed/oversize token, forbidden jku/x5u/jwk/crit, wrong/missing typ, ID-token confusion => reject, no user/session.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U06

**Fixture, tindakan dan expected:** Exact issuer wrong/untrusted/inactive/ambiguous or wrong DB/provider binding; absent/revoked/mismatched/duplicate kid and missing/ambiguous backend; caller-injected key reference => reject, never fallback. Apply selected local kid contract explicitly.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U07

**Fixture, tindakan dan expected:** Missing/wrong/malformed iss, aud (empty, mixed invalid, nonmatching), exp, iat, jti, sub, client_id; future iat/nbf, expired or exact boundary; optional nbf absent accepted only per agreed policy; strict claim typing and issuer/aud/client/azp independence. Each negative rejects.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U08

**Fixture, tindakan dan expected:** Matching single/list audience, configured allowlist with one matching value, correct client_id, allowed azp present or explicitly allowed absent; mismatch, malformed, absent when required => reject. Never equate aud, client_id and azp.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U09

**Fixture, tindakan dan expected:** Unknown/ambiguous/disabled user, invalid binding, duplicate mapping, wrong company, portal/public/share/superuser, inactive and policy revision changed mid-validation => deny; fabricated or modified verified dict and wrong request context denied.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U10

**Fixture, tindakan dan expected:** Rotation: provision new key through selected trust-admin path; explicitly retain old key for approved window, validate both while allowed, switch signer, revoke/remove old then reject old and unknown kid; duplicates and stale cache fail closed; no private-key exposure. Validate expiry policy/backup/rollback per decided contract.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U11

**Fixture, tindakan dan expected:** Failure isolation: no profile/provider, malformed key, policy mutation, ambiguous issuer, backend exception and disabled integration deny; existing remote configured profile still uses its established path and validation; no recursion in real merged registry/MRO and bounded backend call count.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U12

**Fixture, tindakan dan expected:** Network oracle: instrument outbound HTTP client/transport plus process/socket egress for the entire selected validation call, including classification, discovery, JWKS/key and exception paths. Positive + negatives and unavailable provider: zero introspection AND zero outbound self-provider requests; retain captures/counters and prove observer with a controlled known request in separately authorized setup. Scope does not forbid unrelated traffic or remote validation; distinguish normal frontchannel and test harness.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U13

**Fixture, tindakan dan expected:** Security/operations: only trust-admin can change binding/key/algorithm; ordinary users cannot spoof profile or fetch private material; sanitize logs/response, no bearer/key/secret leakage; policy revisions invalidate stale provenance.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U14

**Fixture, tindakan dan expected:** Install graph and contracts: no hard reverse dependency/import; verify selected optional composition, native registry, existing helper API/return types, disabled failure and legacy consumers without implicit trust. If upgrade/rollback becomes in scope, obtain separate requirements, authorization and evidence; no claim now.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U15

**Fixture, tindakan dan expected:** Issuance security: unauthorized caller cannot set arbitrary sub/client_id/iss/alg; valid issuance generates fresh jti, approved iat/exp and typ, client identity derives from authenticated context; generic JWT, forged claim and replay-policy expectations per decision.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### U16

**Fixture, tindakan dan expected:** Pada kandidat tepat dan Odoo 13 / CPython 3.7.3 yang disetujui, verifikasi dependency closure serta instalasi/import, jalankan unit dan native integration suites yang berlaku, periksa API cryptography/PyJWT dan nama manifest; rekam command, jumlah, hasil, runtime dan dependency aktual. Jangan mengasumsikan kompatibilitas dari pin atau interpreter lain.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V09-RT1

**Fixture, tindakan dan expected:** Pada runtime immutable Odoo 13 / CPython 3.7.3 yang disetujui, jalankan workflow dan selector yang diotorisasi; rekam identitas image/digest, interpreter yang benar-benar menjalankan Odoo, resolusi seluruh dependency, command, exit dan log tersanitasi. Buktikan kompatibilitas package/API, jangan menyimpulkan dari label.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V09-RT2

**Fixture, tindakan dan expected:** Konfigurasi final yang diajukan untuk persetujuan memilih nama dan identitas Odoo, PostgreSQL, project, network, volume dan database beserta perannya; tidak ada nama bawaan yang otomatis disetujui. Sebelum mutasi, verifikasi identitas, kepemilikan dan isolasi target nonproduksi; ikat command, selector dan dependency tepat ke image/sumber 3.7.3 yang disetujui. Catat ID resource milik run, termasuk jalur gagal; cleanup hanya resource itu lalu readback masing-masing ID dan eskalasi sisa atau ketidakpastian.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

### V09-RT3

**Fixture, tindakan dan expected:** Identifikasi dan pertahankan bukti CPython 3.7.9 sebelumnya beserta kandidat, runtime, provenance dan actual aslinya; jangan mengubah actual atau melabelinya sebagai bukti 3.7.3. Perbedaan catatan actual yang belum direkonsiliasi tetap terbuka. Tidak ada klaim kompatibilitas tanpa eksekusi pada runtime immutable 3.7.3 yang disetujui dan bukti dependency serta hasilnya.

**Bukti:** identitas fixture/actor dan komposisi, aksi, nilai/assertion expected versus actual dan bukti tersanitasi sesuai prasyarat bersama; sertakan readback/observer yang disebut pada kasus. **Actual: NOT RUN.**

## Penilaian dan handoff

Normal ACCEPT mensyaratkan seluruh kasus yang berlaku benar-benar PASS dengan bukti yang memadai, termasuk gate administratif dan runtime. FAIL, PARTIAL atau BLOCKED tidak menjadi PASS karena statis, mock, ringkasan atau persetujuan spesifikasi. Hanya Owner dapat memberi waiver eksplisit dengan setiap deviasi dan follow-up; actual tidak diubah. Penerimaan risiko, izin eksekusi, PR, merge dan deployment adalah keputusan tersendiri.

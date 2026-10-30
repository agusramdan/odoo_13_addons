# QA independen — ADDONS13-64 Step 0 / rebase

## Verdict

**PASS — terbatas QA dokumen Step 0 dan kesetaraan rebase Git.** Tidak ditemukan temuan kritis dalam lingkup ini. **Bukan PASS UAT, bukan Owner acceptance, bukan izin implementasi/Step 1, PR, merge, atau release.** Seluruh 24 kasus kandidat baru tetap NOT RUN. Blocker dependency dan keputusan produk/runtime tetap terbuka.

Tester hanya membaca Git/source/dokumen lokal, dengan `GIT_OPTIONAL_LOCKS=0`; tidak menjalankan aplikasi, tests, install, resolver, rebase, fetch, push, atau operasi Plane. Satu-satunya file yang dibuat oleh QA adalah laporan ini, di luar repository/worktree.

## Kandidat dan otoritas dokumen

- Worktree: `/home/ubuntu/worktrees/ADDONS13-64`.
- HEAD aktual: `3774c6fda99aab9b5f3d03241a4a876d1cb493b1`.
- Target `origin/main` aktual: `ac1bcbd66261b92c10078f2a8744a657a3b6490c`.
- Feature sebelum rebase: `eaf2c7f016ad9c0ae7945528529e0b73727bed4c`.
- Base lama: `5de9a5776aecf8383ce580ed0446ee470f1c5425`.

Otoritas draft kandidat sekarang adalah **PRD-REBASED-DRAFT.md dan UAT-REBASED-DRAFT.md**, khususnya bagian akhir **“Binding kandidat pasca-rebase oleh Lead”**. Keduanya menyebut HEAD/target yang benar dan tetap DRAFT / NOT ACCEPTED. Binding secara eksplisit menyupersede narasi pending/pra-rebase serta informasi Plane yang belum dibaca pada tahap awal. Karena itu kutipan provenance lama tidak dinilai sebagai kandidat kini masih belum terikat.

`PRD-DRAFT.md`, `UAT-DRAFT.md`, `STEP0-REPORT.md`, `VERIFICATION.json`, `EVIDENCE-SNAPSHOT.json`, dan `SHA256SUMS.txt` adalah artefak analisis pra-rebase yang dipertahankan. Khusus `VERIFICATION.json` yang menyebut candidate null/rebase false bukan hasil verifikasi terbaru. `REBASE-REPORT.md` mencatat tahap Git sebelum binding Lead, bukan mencabut binding terbaru. Penerimaan exact-hash kedua draft baru **belum terjadi**.

### SHA-256 dihitung ulang

| Dokumen kandidat | SHA-256 aktual |
|---|---|
| PRD-REBASED-DRAFT.md | `15f8e36979fd56dc70542a72b2a28156886da01777aeb31d95b4c09803fd422f` |
| UAT-REBASED-DRAFT.md | `d68fbc2f07e72a243404897d75c47aeaca50ef6cd7ad79af278e1148aa8cba8f` |

Keduanya cocok dengan hashes kandidat yang diberikan kepada QA. Kelima entry manifest lama `SHA256SUMS.txt` cocok dengan file aktual; kedelapan hash artefak historis dalam `EVIDENCE-SNAPSHOT.json` juga cocok. Manifest lama tidak mencakup dua draft rebased; hashes kandidat di atas yang menjadi rujukan review baru, bukan manifest pra-rebase.

## Hasil verifikasi Git independen

Perintah read-only yang digunakan: `rev-parse`, `merge-base --is-ancestor`, `rev-list --count`, `range-diff --no-color`, `show`, `patch-id --stable`, `diff --name-only`, `diff --check`, `for-each-ref`, `worktree list --porcelain`, `symbolic-ref`, `status --porcelain=v1 -z --untracked-files=all`, serta pembacaan binary/full-index diff dan hash file dirty.

| Pemeriksaan | Hasil |
|---|---|
| Target ancestor HEAD | exit 0 |
| Jumlah commit feature sebelum/sesudah | 8 / 8 |
| Range-diff | 8 tanda `=`, tanpa perubahan patch; identik dengan REBASE-EVIDENCE.json dan REBASE-RANGE-DIFF.txt |
| Stable patch IDs | Delapan ID sama dalam urutan yang sama pada series lama dan baru |
| Path feature relatif base masing-masing | Tepat 32, set/urutan sama dengan snapshot sebelum dan evidence sesudah |
| Path `amr_resource/` pada diff target → kandidat | 0 |
| `diff --check target HEAD` | exit 0, tanpa keluaran |
| Feature worktree | clean, branch ADDONS13-64 |
| Lima local non-feature refs | Semua sama dengan REBASE-BEFORE.json |
| Tujuh worktree | Membership dan branch sama; semua HEAD non-feature, status, staged/unstaged diff hashes serta identitas file dirty sama dengan snapshot sebelum |

Branch lain tetap: ADDONS13-65 `24a2824837cff80a08bdb32f40d89fd20eb7ec96`; ADDONS13-65-PR `44302edbdc2a2c4c3509a09321028f64302e66f9`; ADDONS13-67 `61140b3b75b9186771e32a9cd107095d6fbe754e`; ODOO13-SKILLS13 `7449debb1ee2b9780e3f8568c813be0b772cfa5e`; main `c08b050cfd85ccc5c705eb92852e57626eb82806`.

ADDONS13-65 tetap **`AD skills/UPSTREAM-SOURCE.txt`**, file working-tree tetap absent, staged hash `fbc533038ba4e44f05f2f02947de43f27aa130d02e4142a91c4d8ad3d8bf70ba` dan unstaged hash `be5516c90cb18cef5ac60b5e4bb6609bdedb1810a52c63fe5d2755f4642f04c4` cocok snapshot. Detached sibling rev03 tetap pada `a1ce446dc7f7bbcc55d2dcf0a6d36cee9d0009f4`, termasuk dua file dirty dan hashes-nya. Tidak dibersihkan atau diubah.

Seluruh **36 entry source inventory** diverifikasi programmatically terhadap revision historis yang dipin (HEAD historis diterjemahkan ke eaf2c7f, origin/main ke target SHA), termasuk dua entry deleted. Blob/hash cocok; isi atau ketidakhadiran path tersebut pada kandidat baru juga cocok. Ini mendukung bahwa perubahan upstream amr_resource ikut target, bukan tambahan scope feature. Diff upstream memang menghapus seed PS256 dan mengubah dua model dari direct RegistryAccess subclass menjadi models.Model dengan `_inherit = 'amr.resource.registry.access'`; tidak membuktikan runtime install berhasil.

## AC ↔ UAT: hasil parsing programmatic

Baris matriks diparse dari Markdown, bukan dihitung manual. Ditemukan **24 baris, 24 ID unik, tepat UAT-01 sampai UAT-24**, semuanya **NOT RUN**. Setiap AC dalam PRD diparse termasuk rentang en-dash, lalu dibandingkan dengan kolom AC matriks UAT: **seluruh pemetaan dua arah cocok**. AC-09 diwariskan ke semua kasus sesuai ketentuan UAT baris 12.

| AC | Kasus | Jumlah |
|---|---|---:|
| AC-01 | 01, 18 | 2 |
| AC-02 | 02, 03, 04, 05, 09, 20 | 6 |
| AC-03 | 06, 07, 08, 21, 22 | 5 |
| AC-04 | 17, 19, 23 | 3 |
| AC-05 | 11, 12, 13, 14, 15 | 5 |
| AC-06 | 16 | 1 |
| AC-07 | 10, 20, 24 | 3 |
| AC-08 | 18, 24 | 2 |
| AC-09 | seluruh 01–24, inherited | 24 |

Semua kasus memiliki prasyarat, langkah, expected/oracle, dan status; expected tidak dipresentasikan sebagai actual. UAT membedakan SDK mock/nyata, registry dan effective override, restart/multi-registry, telemetry versus business failure, privacy explicit capture versus global SDK integration, resolver, serta rendered UI sebagai subcriterion tersendiri.

## Konsistensi source, dependency dan evidence historis

- Source `config.py`, `runtime.py`, `sentry_reporting.py`, optional manifest dan bridge ORM mendukung klaim file path default/override, YAML/JSON, namespace wajib mapping, policy keys enabled/mode, gate mode/enabled/DSN, process import bootstrap, generic warnings, best-effort capture, optional inheritance, dan tidak adanya explicit body/header/customer attachments. Loader mengizinkan extra top-level keys, sesuai catatan draft. Import yaml berada sebelum exception handler runtime; keterbatasan missing declared dependency ini sudah dinyatakan, tidak disembunyikan.
- Requirements aktual optional addon mem-pin `sentry-sdk==2.73.0` dan `PyYAML==6.0.1`; root mem-pin `requests==2.31.0`. Tidak ada klaim bahwa root pins menyelesaikan kompatibilitas image historis Odoo.
- Metadata dibaca langsung dari dua wheel lokal historis, **tanpa mengimpor/menginstal package**. SDK SHA-256 `0bcfa6928ea5adbb89591858b514d27adac27c7a3cccc31b20ed10e0b09eda9e`: `Requires-Python: >=3.6`, `Requires-Dist: urllib3>=1.26.11`. Requests 2.21.0 SHA-256 `7bf2a778576d825600030a110f3c0e3e8edc51dfaafe1c146e39a2027784957b`: `Requires-Dist: urllib3 (<1.25,>=1.21.1)`. Constraints tidak beririsan; dependency acceptance tetap BLOCKER, bukan FAIL rebase/dokumen karena draft sudah menyatakannya dan belum meminta runtime PASS.
- `UAT-RESULTS.json` dihitung ulang: **21 ID unik, 9 PASS, 11 NOT RUN, 1 PARTIAL**, pada eaf2c7f + dependency commit `21b5a81560acc2efadbfcf423e60523cd01a6b60`, composition hash `0ea7a2fb3ed636e011a1a65990c2b452e7b5dba579d7eff3fa132bfa08d22827`. Bukan clean rebased candidate.
- `UAT-20-results-final.json` aktual tetap PARTIAL. Snapshot komentar Plane lokal diparse: **19 hasil, 19 ID unik, total_count 19, next_page_results false**. Komentar terbaru mengikat waiver hanya rendered-browser subcriterion UAT-20 ke **eaf2c7f**, bukan seluruh kasus dan bukan kandidat baru. Tester tidak mengakses Plane live; pembacaan live oleh Lead dinilai melalui snapshot yang tersedia.

## Temuan dan tindak lanjut

**Temuan kritis lingkup QA ini: tidak ada; tidak ada exact fix wajib untuk rebase/draft.** Tidak ada runtime/test result baru yang boleh diturunkan dari laporan ini.

Catatan editorial non-blocking: PRD rebased masih memuat narasi pra-rebase di pembukaan/body dan laporan lama memakai pending metadata. Binding akhir sudah eksplisit mengatasi itu. Untuk kenyamanan pembaca, revisi mendatang dapat menambahkan penunjuk binding terbaru di bagian paling atas; jika diubah, hitung ulang hashes dan minta penerimaan exact-hash lagi. Jangan mengedit artefak historis accepted.

Sebelum gate berikutnya: Owner/Lead menerima atau merevisi dua draft exact-hash; putuskan dependency set, batas global SDK versus explicit service reporting, dan gap kompatibilitas helper/metadata; barulah minta otorisasi runtime/UAT terpisah. Laporan ini tidak melakukan atau memberi otorisasi tindakan tersebut.

Catatan alat: satu audit source awal berhenti karena mencoba `git show` pada path yang memang tercatat deleted. Pemeriksaan diperbaiki agar memverifikasi ketidakhadiran path deleted; rerun seluruh 36 entry selesai tanpa mismatch. Tidak ada runtime/test/install yang dijalankan sebagai akibatnya.

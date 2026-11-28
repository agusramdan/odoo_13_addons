# Laporan QA amr_resource

## Unit dan coverage

`sh .agents/skills/odoo-unit-test/scripts/run_tests_in_docker.sh --coverage --coverage-min 50 --addon /workspace/amr_resource` — exit 0; Python 3.7.3; **45 passed**, 3 warning. Coverage line **63%**, 1.142 statement, 417 missed; source Python seluruh addon termasuk manifest dan `__init__.py`, mengecualikan tests/fixtures. Denominator dan pengecualian belum disetujui owner; angka bukan keputusan gate acceptance. Unit memakai mock, bukan bukti ORM.

## Runtime dan blocker jwt

`python3 .agents/skills/odoo-browser-test/scripts/run.py --addon /workspace/amr_resource --test TestIssuerBrowser.test_children --timeout 600` — exit 1; Odoo 13 gagal install addon sebelum test: `Python library not installed: jwt`, count 0. Image browser standar berbasis `odoo:13.0` tidak menyediakan PyJWT; manifest memang mensyaratkan `jwt`.

Workaround QA terisolasi: `.runtime/Dockerfile` memakai image unit yang dibangun dari `.devcontainer/Dockerfile.unittest` dan `requirements.txt` proyek (PyJWT 2.8.0, cryptography 39.0.2), menambah Chromium dan websocket, mengembalikan entrypoint Odoo. Tidak mengubah dependensi proyek. `.runtime/qa_runner.py` salinan runner browser, satu-satunya perbedaan efektif lokasi konteks build. Database PostgreSQL tmpfs, jaringan internal, tidak ada port host; runner membersihkan resource berlabel tiap run. Log di `.runtime/browser_*.log`.

## Integrasi Odoo 13

`python3 .runtime/integration_runner.py --addon /workspace/amr_resource --test TestIssuerLifecycle.test_matrix_and_search_context --timeout 600` — exit 0; runner turunan tersebut memilih **seluruh class** `TestIssuerLifecycle` (argumen method hanya memenuhi validasi CLI); 9 test berjalan, 0 failure/error, termasuk batch atomicity, transisi, guard anak dan akses/view. Log `.runtime/integration_all.log`. Ini tes integrasi terisolasi, bukan UAT. Percobaan sebelumnya dengan selector method juga menjalankan 1 test sukses (`.runtime/integration.log`). Output sukses generik runner menyebut browser tetapi tidak berlaku untuk integrasi.

## Browser Odoo 13

Perintah: `python3 .runtime/qa_runner.py --addon /workspace/amr_resource --test TestIssuerBrowser.<method> --timeout 600`.

- `test_children`: 1 lulus; edit empat One2many dan readonly production/disable. Belum menguji tambah/hapus via UI; AC tersebut **NOT RUN**.
- `test_lifecycle`: 1 lulus.
- `test_draft_form`: 1 lulus.
- `test_nonadmin_access`: 1 lulus.
- `test_archive_reactivation`: **FAIL**, 1 failure; `Timeout: action menu` setelah arsip dan reopen. Belum dapat menyimpulkan apakah selector atau UI penyebab; unarchive browser dan transisi selanjutnya belum terverifikasi. Lihat `.runtime/browser_archive.log`.

Tambah/hapus UI empat One2many belum dilengkapi; membutuhkan implementasi dan pengujian browser lanjutan. Tidak ada klaim UAT atau acceptance. `git diff --check` lulus. Tidak ada commit.

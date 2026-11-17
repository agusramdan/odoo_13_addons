# ADDONS13-71 — Trace DRAFT refaktor Owner v2

Status acceptance=false; source review statis, seluruh test NOT RUN. Owner meminta refaktor dimasukkan PRD/UAT; bukan persetujuan silent remapping, default outbound, risiko tambahan, atau hasil test. V2 menggantikan arah rekomendasi v1 untuk prospek draft, tidak mengedit v1 maupun acceptance historis.

## Provenance terverifikasi
- Worktree `/home/ubuntu/worktrees/ADDONS13-71`, branch `ADDONS13-71`, HEAD `284f51a6fd26e0d33494f5a6216df8776ad55d2a`; status dan index sebelum pembuatan clean; v2 belum ada. Checkpoint `7e6106428113a8540d484c216dfa6583a18d4a3b`, parent `9bdd35c3d7281969270943dd16e9d4d8758615f9`; source checkpoint vs HEAD tidak berbeda. `amr_service_client/models/service_client.py` SHA-256 `da089e3c52d04dcdc089cd62cec62f505efa15fe165e149df23fc305473061c1`.
- Accepted predecessor `/home/ubuntu/docs/reports/ADDONS13-71/analysis-v1/PRD-DRAFT.md` SHA `a8f39e9bac135b0228e599e552423ee498eb525211713e086869f0ff26365ead`, `UAT-DRAFT.md` SHA `85a55bbb2ce23f7484e54c6c1f7b4bca4695ae8515db34db1484dbbbf18a4d80`; `LEAD-ACCEPTANCE-OWNER-v1.md` pasal 15–20 mencatat penerimaan snapshot.
- Accepted `/home/ubuntu/docs/reports/ADDONS13-71/amendment-url-headers-v1/PRD-AMENDMENT-DRAFT.md` SHA `0b7bb752aed021ad3edc4d021032c96a2d110145f75067e8d1c68a36ada20c72`, `UAT-AMENDMENT-DRAFT.md` SHA `7eadd09c9f044e41a9091070075dfaa977acff1b17a983b4be1af96bdc99fc88`, `OWNER-ACCEPTANCE-v1.md` SHA `7cfc24449a32f845478d7f2c28f3109a6ac39b219a2df745f4029036e0f5ebfe`.
- Refactor v1 sebelum revisi: `ANALISIS.md` SHA `95cf00912a10e348890a92f6f320bb75a209a55f05765ade387c3d115f5bc0a1`, `PRD-AMENDMENT-DRAFT.md` SHA `1e68f2d51d85de3ddc7d5184bb115ac1bc26ef0e6c41149327c7c6c3d1e391e3`, `UAT-AMENDMENT-DRAFT.md` SHA `55aebe49e8292dbbf8dc544f669c11306519cf219195e72ae0b73cf2f1a0d28c`. Hash v2 tersedia di SHA256SUMS; manifest tidak meng-hash dirinya.

## Source → fakta → requirement → kasus
| Lokasi source | Fakta statis pada checkpoint | Usulan / risiko / kasus |
|---|---|---|
| `service_client.py:104–160,165–180,252–254` | sender dispatch, flag snapshot, writer, return dan hook | P0/C06 → R05, R10, R12; U01–U14 masing-masing |
| `:189–207,218` | header `kw.get('headers') or {}` sebelum normalizer; URL/params/header omission, audience dan provider | C02/P1/C06 → R01, R10, R11; A01–A07/AU01–AU15; **AU10 None eksplisit diusulkan berubah**, AU08 tidak otomatis berubah |
| `:208–217,124–160` | prioritas method lalu GET; JSON hanya POST/PUT/PATCH; dispatcher memakai preparation | C03/D3 → R03, R05, R06, R10; outbound dan hasil log baru belum disetujui |
| `:225–250` | `call(raise_exception=True,**kw)`, setelah provider method untuk report; wrappers menggunakan keyword | C01/C04, D1/D4 → R02–R03, R06–R07, R09–R10; potensi amendemen R4/U14 direct-call |
| `:528–544,282–301` | action default POST dan proxy post | P0/C01/C06 → R06, R09–R10 |
| `:597–641` | factory call **kw, path optional call/get/post/put, delete required; audience keyword forwarded | C05, D1/D5 → R04, R08–R10; ekspansi factory dan positional audience belum diterima |

## Coverage dua arah
| PRD invariant/AC | Kasus UAT |
|---|---|
| P0 | R05, R10, R12; U01–U14 |
| P1 | R01, R06, R10, R11; AU01–AU15 |
| P2 | R10; AU13–AU14 adalah demonstrasi kompatibilitas yang diharapkan, bukan bukti deployment aman; risiko tujuan URL dinilai sebagai risiko yang diterima, bukan diuji tuntas oleh seam |
| C01 | R02–R04, R09–R10 |
| C02 | R01, R10; AU08–AU11, khusus AU10 None |
| C03 | R03, R05–R06, R10 |
| C04 | R07, R10; direct-call U14/R4 bersyarat |
| C05 | R04, R08–R10 |
| C06 | R10–R12; semua U01–U14 dan AU01–AU15 termasuk AU15 |

Seluruh R01–R12 dipetakan ke setidaknya satu AC di atas. Skenario cabang D1–D5 hanya dapat menjadi oracle final setelah Owner memilih dan detail tersisa ditetapkan. Eksekusi native, DB, jaringan, test atau acceptance tidak dilakukan. Sejarah review tidak diubah; Lead menangani Git pada transisi step.

# Pengecualian cakupan RPC

- Keputusan owner sesuai instruksi dan `.runtime/spec.md`: enforcement dan pengujian RPC di luar cakupan saat ini. Tidak ada klaim keamanan atau keberhasilan RPC. Guard ORM issuer dan regresi guard anak tetap dalam cakupan pengujian yang disetujui.
- Pengecualian RPC tidak membuktikan pengujian RPC berhasil. Denominator coverage dan pengecualian tests/fixtures masih memerlukan konfirmasi owner.

# Waiver item UAT yang belum diuji

Owner meminta item yang belum diuji dicatat sebagai waiver. Status berikut tetap NOT RUN, bukan PASS:

1. Tambah dan hapus masing-masing empat relasi One2many pada draft melalui browser.
2. Verifikasi seluruh field parent yang sebelumnya editable melalui browser.
3. Verifikasi UI menggunakan akun trust admin khusus dan cakupan ACL secara lengkap.

Cakupan waiver terbatas pada pengujian di atas. Alasan spesifik dan task tindak lanjut terpisah untuk setiap item belum diberikan; perlu keputusan owner sebelum gate UAT dinyatakan ACCEPTED_WITH_WAIVER. Permintaan ini tidak mengonfirmasi denominator coverage atau pengecualian tests/fixtures.
- Tindak lanjut: bila jaminan RPC diperlukan, owner perlu menyetujui task terpisah untuk spesifikasi, implementasi dan pengujian batas RPC.

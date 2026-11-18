
task:
- Kerjakan hanya addons amr_resource model sudah dibuat field tidak perlu di tambah.
- Pastikan model oidc.issuer.register beserta anak-anaknya hanya bisa di edit pada kondisi darft.
- Buatkan button action agar berpindah state.
- Unit Test Coverage 50%
- Matriks transisi status, `disable` dapat diaktifkan kembali menjadi `production` atau kembali ke `draft`. 
- Hanya status `disable` bisa melakukan unlink akan menjadi inactive.

Rule:
- Odoo 13
- agent menulis document spec.md, test_plan.md , test_report.md, review_report.md, waiver.md di directory .runtime
- Pembatasan enforcement melalui RPC/ORM langsung di luar cakupan saat ini.

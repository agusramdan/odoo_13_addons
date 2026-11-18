# Verifikasi browser 2026-11-27

Docker daemon bersama; tidak ada restart, perubahan konfigurasi, atau prune. `docker run --rm --network none alpine:latest true` exit 0. `printf 'FROM alpine:latest\nRUN true\n' | timeout 45 docker build --label odoo.browser.run=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb -t odoo-browser-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb:local -` exit 0: RUN dan LABEL selesai. Timeout build sebelumnya tidak terulang; penyebab tidak diketahui. `DOCKER_BUILDKIT=1` gagal: buildx tidak terpasang; default legacy builder berhasil tanpa perubahan sistem. `docker build --progress=plain` tidak didukung legacy builder. Tidak ada dasar meminta tindakan administrator untuk build yang sekarang berhasil.

- `python3 -m unittest discover -s .agents/skills/odoo-browser-test/tests -v`: 10 lulus.
- `python3 .agents/skills/odoo-browser-test/scripts/run.py --addon /workspace/.agents/skills/odoo-browser-test/fixtures/browser_probe --test BrowserProbe.test_positive --timeout 600`: exit 0, `Ran 1 test`, `docker_exit=0`, Chrome headless, reported success. Run ID `9a0993a9610b41d497892f485694f09c`.
- Perintah sama dengan `--test BrowserProbe.test_negative`: exit 1, `Ran 1 test`, `docker_exit=1`, `1 failures, 0 errors`, `intentional negative control`. Run ID `f40cd65a24e44e2f88985f3d7d43432e`.
- `python3 .agents/skills/odoo-browser-test/scripts/run.py --recover ID` dijalankan untuk kedua run dan probe build ID `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, `cccccccccccccccccccccccccccccccc`. Pemeriksaan `docker ps -aq`, `docker network ls -q`, `docker image ls -aq` dengan filter label `odoo.browser.run=ID`: kosong untuk keempat ID. Cache build dan image dasar bukan cakupan cleanup.

Fixture hanya uji sintetis, bukan UAT; PostgreSQL menggunakan tmpfs terpisah sesuai runner. Output negatif sementara: `/home/dev/.hermes/cache/scratch/odoo-browser-negative.log`.

# Membangun Workflow Agentic AI yang Terisolasi: Sinergi DevPod dan Hermes Agent

Cara tim *software engineering* berinteraksi dengan AI sedang bergeser cepat—dari sekadar *autocomplete* di editor menuju **Agentic AI** yang mampu membaca *codebase*, merancang solusi, menulis kode, menjalankan *test*, hingga melakukan *code review* secara mandiri.

Namun, menjalankan *coding agent* otonom langsung di laptop lokal atau di satu server VPS yang dipakai bersama menyimpan banyak risiko: konflik *dependency*, *state* Git yang berantakan, konsumsi RAM tak terkendali, hingga risiko keamanan jika agen mengeksekusi perintah shell yang keliru.

Untuk menjawab tantangan tersebut, menggabungkan **DevPod** sebagai lingkungan kerja terisolasi dengan **Hermes Agent** sebagai motor eksekusi AI memberikan fondasi arsitektur yang disiplin, aman, dan mudah direplikasi.

---

## 1. Mengapa Harus Menggabungkan DevPod dan Hermes Agent?

Secara sederhana, kolaborasi keduanya memisahkan **infrastruktur eksekusi** dari **kecerdasan orkestrasi**:

* **DevPod (Sandbox & Reproducibility):** Mengubah file `.devcontainer/devcontainer.json` dan Docker Compose menjadi *workspace* container yang bersih, konsisten, dan bisa dihancurkan kapan saja setelah tugas selesai.
* **Hermes Agent (Otak & Eksekutor):** Berjalan di dalam *workspace* tersebut dengan akses langsung ke *source code*, terminal, dan *tools* lokal untuk menyelesaikan tugas *engineering* secara terstruktur.

Dengan pola ini, agen AI tidak lagi bekerja secara "buta" di luar lingkungan aplikasi—ia bisa langsung menjalankan *build*, memverifikasi *log*, dan mengeksekusi *automated test* di lingkungan yang identik dengan milik developer.

---

## 2. Prinsip Kerja: "1 Task, 1 Git Branch, 1 Isolated Workspace"

Alih-alih menumpuk banyak pekerjaan di satu server monolitik, pendekatan DevPod + Hermes mendorong isolasi penuh per tugas:

1. **Isolasi *Compute* & Database:** Setiap *task* mendapatkan container aplikasi, database, dan *memory limit* tersendiri. Jika sebuah eksperimen AI membuat proses *hang* atau *database* korup, dampaknya berhenti di container tersebut dan tidak mengganggu *task* lain.
2. **Isolasi Git:** Setiap *workspace* terikat pada satu *branch* khusus. Riwayat *commit* tetap bersih dan mudah dilacak.
3. **Siap Kolaborasi Manusia & AI:** Karena berbasis `.devcontainer`, developer manusia bisa langsung membuka *workspace* yang sama menggunakan VS Code atau JetBrains kapan pun perlu melakukan *intervensi*, *debugging*, atau *review* manual.

---

## 3. Anatomi Hermes Agent dan Pendekatan *Skills-as-Code*

Agar AI tidak berperilaku acak, Hermes Agent memanfaatkan pendekatan konfigurasi berlapis yang disimpan dan di-versi-kan langsung di Git (*Skills-as-Code*):

| Lapisan Konfigurasi | Fungsi Utama |
| :--- | :--- |
| **`SOUL.md`** | Mendefinisikan persona, prinsip dasar, dan batasan perilaku agen. |
| **`AGENTS.md`** | Mengatur aturan main proyek, struktur direktori, serta alur kerja (*workflow*) antar-agen. |
| **`config.yaml`** | Konfigurasi teknis *runtime*, *tool permissions*, dan koneksi ke *LLM Gateway* (seperti LiteLLM). |
| **`SKILL.md`** | Pengetahuan domain dan SOP spesifik (misalnya standar *coding*, pola *testing*, atau prosedur migrasi) yang bisa dipakai ulang lintas proyek. |

Dengan menyimpan seluruh definisi ini di dalam repository Git, pengetahuan tim tidak lagi terjebak di *chat history* masing-masing orang. Setiap perbaikan *prompt* atau SOP langsung menjadi standar baru bagi seluruh agen dan anggota tim.

---

## 4. Orkestrasi Multi-Agent dalam Satu Siklus Tugas

Salah satu kelemahan penggunaan satu agen untuk semua hal adalah konteks yang cepat penuh dan kualitas hasil yang menurun. Di dalam *workspace* DevPod, Hermes dapat diorkestrasi menjadi alur kerja **4 peran spesifik**:

```text
[ Task / Issue ]
       │
       ▼
1. Analyst Agent   ──► Brainstorming teknis, menyusun PRD & kriteria UAT
       │
       ▼
2. Developer Agent ──► Implementasi kode di branch terisolasi berdasarkan PRD
       │
       ▼
3. Reviewer Agent  ──► Static analysis, audit keamanan, & kesesuaian arsitektur
       │
       ▼
4. Tester Agent    ──► Menjalankan automated test & validasi skenario UAT
       │
       ▼
[ Human Review & Merge ]
```

* **Analyst Agent:** Fokus memahami masalah bisnis dan teknis terlebih dahulu sebelum satu baris kode pun ditulis, menghasilkan dokumen spesifikasi (PRD) dan daftar skenario pengujian (UAT).
* **Developer Agent:** Mengeksekusi implementasi secara fokus mengacu pada PRD dan `SKILL.md` proyek.
* **Reviewer Agent:** Bertindak sebagai gerbang kualitas pertama—memeriksa *code smell*, kepatuhan standar, hingga celah keamanan (misalnya terintegrasi dengan *static analysis* seperti Semgrep).
* **Tester Agent:** Memastikan kode benar-benar berjalan di dalam container DevPod dan lolos seluruh pengujian otomatis sebelum diserahkan ke manusia.

---

## 5. Guardrails: Keamanan dan Batas Akses Git

Memberikan otonomi kepada AI harus selalu diimbangi dengan pagar pengaman (*guardrails*) yang ketat:

* **Pemisahan Hak Akses Git:** Agen AI sebaiknya hanya diberi akses **read-only** ke repository utama perusahaan. Untuk *commit* dan *push* otonom, arahkan agen ke *branch* atau repository khusus agen. Penggabungan (*merge*) ke *branch* utama tetap melalui *Pull Request* dan persetujuan manusia (*human-in-the-loop*).
* **Kontrol Biaya & Model via Gateway:** Mengarahkan permintaan LLM melalui *proxy* seperti LiteLLM memudahkan pengaturan *rate limit*, pencatatan penggunaan token per *task*, serta pemilihan model yang tepat untuk tiap peran (misalnya model *reasoning* untuk Analyst/Reviewer, dan model cepat untuk eksekusi rutin).
* **Blast Radius Terbatas:** Karena seluruh perintah terminal dieksekusi di dalam container DevPod tanpa akses *root* ke *host* utama, kesalahan skrip atau penghapusan file tidak akan merusak infrastruktur produksi maupun server utama.

---

## Penutup

Masa depan *software development* bukan tentang menggantikan developer dengan AI yang bekerja tanpa kendali, melainkan membangun **pabrik perangkat lunak mini** tempat manusia dan agen AI bekerja di ruang yang sama dengan aturan yang jelas.

**DevPod** menyediakan *sandbox* yang bersih, seragam, dan terisolasi untuk setiap tugas, sementara **Hermes Agent** menghadirkan eksekusi multi-agen yang terstruktur melalui *Skills-as-Code*. Kombinasi keduanya mengubah penggunaan AI dari sekadar eksperimen *chat* menjadi alur kerja *engineering* yang aman, terukur, dan siap dikembangkan ke skala tim.
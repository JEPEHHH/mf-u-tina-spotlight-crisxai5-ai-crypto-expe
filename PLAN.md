# Rencana Kerja: Spotlight @crisxai5 (AI & Crypto Expert on X)

**Target**: Publikasikan post X dari akun publik dengan visual/video orisinal buatan agen yang memperkenalkan `@crisxai5` (`https://x.com/crisxai5`) sebagai pakar AI & crypto; peringkat ditentukan oleh `likes + reposts + quotes` setelah deadline (`2026-11-27 11:35 UTC`).

## Rencana Kerja
1. **Cek prasyarat**: Verifikasi Node.js >= 22.18, alat render media (`ffmpeg` / generator gambar / Pillow), akses akun X publik, serta `makefun-` play code dari rute kompetisi.
2. **Konsep kreatif & copy**: Putuskan konsep visual/video pendek yang jelas di layar ponsel (fokus pada AI agents, crypto alpha, Web3 tooling, on-chain automation) dan susun teks post berisi `@crisxai5`, `https://x.com/crisxai5`, 3–5 hashtag (`#AI #Crypto #AIAgents #Web3`), dan play code `makefun-...`.
3. **Produksi aset di sesi agen**: Render gambar (PNG/JPEG) atau video (MP4 H.264/AAC <= 140 dtk) langsung di sesi ini agar tercatat di transkrip, lalu periksa hasil render hingga tajam dan bebas kesalahan.
4. **Siapkan berkas root repo**: Buat `main.ts` (salin `POST.json` ke `/output/POST.json` secara deterministik tanpa jaringan), `LICENSE` (OSI-approved), `README.md`, dan `POST.json`.
5. **Publikasi & catat tautan**: Unggah media secara native bersama teks post ke X publik dalam jendela kompetisi, lalu tulis URL post ke `POST.json`.
6. **Validasi & commit**: Jalankan uji deterministik `MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts`, verifikasi dengan `makefun.mjs check` beserta transkrip sesi, dan commit tiap milestone.

## Daftar Berkas yang Akan Dibuat
- `main.ts` — Program Node 22 di root repo yang menyalin `POST.json` ke `/output/POST.json`.
- `POST.json` — Alamat post X publik dalam format `{"url": "https://x.com/<handle>/status/<id>"}`.
- `LICENSE` — Lisensi OSI-approved (MIT) sesuai syarat kompetisi.
- `README.md` — Dokumentasi singkat entri, cara uji lokal, dan ringkasan aset kreatif.
- `post_copy.txt` — Teks final post X (memuat `@crisxai5`, link profil, hashtag, dan `makefun-` play code).
- `assets/spotlight_crisxai5.png` (atau `.mp4`) — Aset visual/video orisinal buatan agen untuk unggahan X.
- `scripts/generate_asset.py` (opsional) — Skrip pembangkit/komposisi media jika render dilakukan secara terprogram.

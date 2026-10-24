# Wayan

Avatar anak Bali beranimasi, bisa bicara (Azure suara Brian), berekspresi, melambai, jempol, dan merapikan udeng.
Dibuat di Rive (file `wayan`), ditampilkan lewat halaman web.

## Menjalankan

```bash
python3 server.py            # lalu buka http://127.0.0.1:8765
PORT=8766 python3 server.py  # port lain
```

Kunci Azure ada di `.env` (contoh: `.env.example`). Kunci tidak pernah dikirim ke halaman; server hanya memberi token 10 menit.

## Isi folder

| Folder | Isi |
|---|---|
| `web/` | Yang dipakai halaman: `index.html`, `wayan.riv` (hasil export Rive), lapisan latar `bg_*.svg`. `preview.html` = halaman uji animasi Rive (ekspresi, mulut, binding). |
| `assets/vector/` | Sumber gambar karakter dan latar (SVG). `wayan_master.svg` = Wayan utuh; `*_raw.svg` = hasil vectorize mentah sebelum dibersihkan. |
| `assets/drafts/` | Gambar hasil generate (Gemini / Recraft) yang menjadi dasar SVG di atas. |
| `assets/preview/` | Halaman review per animasi (frame, perbandingan) yang ditautkan dari ROADMAP. |
| `references/` | Gambar acuan dan mask untuk generate. Lihat `references/README.txt`. |
| `scripts/` | Skrip pembangun dan penguji rig (daftar di bawah). |
| `docs/` | `PRD.md` (rancangan), `ROADMAP.md` (kemajuan dan keputusan), `prompt-*.md` (prompt yang dipakai), `panduan-bone.svg`. |

## Skrip

| Skrip | Fungsi |
|---|---|
| `recraft.py`, `prep_bg.py`, `strip_bg.py` | Pipa aset: generate/vectorize di Recraft, ganti dan buang latar kunci |
| `rive_mcp.py`, `export_riv.sh`, `rive_frames.py` | Bicara dengan editor Rive, export ke `web/wayan.riv`, render frame timeline untuk review |
| `head_rig25d.py`, `head_rig25d_svg.py`, `head_turn.py` | Kepala 2,5D berlapis dan binding toleh kepala |
| `svg_tools.py` | Pustaka bersama: baca path SVG, ratakan titik, tulis perintah Rive, pilih warna palet |
| `hands_to_rive.py`, `pose_to_rive.py` | Memasukkan tangan dan pose gambar ke rig |
| `salam_keys.py`, `jempol_keys.py` | Keyframe Om Swastiastu dan jempol |
| `udeng_geom.py`, `udeng_rig.py`, `udeng_arm.py`, `udeng_keys.py` | Rig dan keyframe udeng merosot |
| `bg_layers.py` | Memecah `assets/vector/bg_rumah.svg` jadi lapisan latar di `web/` |

Skrip yang bicara dengan Rive butuh editor Rive terbuka pada file `wayan`. File titik (`.head25.json`, `.udeng.json`) menyimpan id objek Rive untuk skrip-skrip itu.

## Riwayat

Percobaan yang ditolak (kepala 3/4, morph kepala, konsep awal, latar lain, uji coba lama) dihapus pada 2026-10-24 dan masih ada di riwayat git sebelum commit pembersihan.

# Prompt — Tangan & pose silang tangan

Dipakai di **aplikasi Gemini (gratis)**, dikerjakan Rozi. Hasilnya lalu di-crop dan di-vectorize lewat Recraft (`scripts/recraft.py vectorize`, $0.01 per gambar, **izin dulu**), dan latar birunya dibuang dengan `scripts/strip_bg.py`. Jalurnya sama dengan master Wayan.

Ada dua gambar terpisah:

| # | Isi | Lampirkan di Gemini | Dipakai untuk |
|---|---|---|---|
| 1 | Lembar 6 bentuk tangan kanan | `references/wayan-gemini-blue-crop.png` | Ditempel di ujung lengan, ditukar per aksi seperti mulut. Tangan kiri = cerminan tangan kanan di Rive |
| 2 | Wayan full body bersilang tangan | `references/wayan-gemini-blue-original.jpeg` | Hanya bagian lengan bersilang + dada yang diambil, lalu ditukar dengan lengan biasa saat pose bosan |
| 3 | Wayan full body tangan menyatu (Om Swastiastu) | `references/wayan-gemini-blue-original.jpeg` | Sama seperti #2: lengan + tangan menyatu + dada ditukar saat salam pembuka (Fase 5b) |

Biaya vectorize: gambar 1–2 sudah ($0.02, 2026-10-21). Gambar 3: **$0.01**, izin dulu.

## Prompt 1 — Lembar tangan

```
Using the attached character as the exact style reference, draw a sheet of
six separate cartoon RIGHT hands for this same boy, in the same flat vector
style: flat solid color blocks, no gradients, no black outlines, no texture,
no shading.

Skin color exactly like his face (#EFAB81). Chunky, soft, rounded cartoon
hands with a thumb and three short thick rounded fingers. Separate the
fingers with a slightly darker skin tone (#D69067) or small gaps, never with
black lines. Each hand ends in a short straight wrist stub, cut cleanly,
with no sleeve and no arm.

The six hands, in a 3 by 2 grid, all the same size, large, well spaced,
none touching or overlapping each other:
1. open hand, palm facing the viewer, fingers slightly spread (waving)
2. thumbs up, knuckles facing the viewer
3. index finger pointing straight up, other fingers curled
4. relaxed closed fist, front view
5. open hand seen from the side, fingers together, palm facing up
   (shrugging or presenting)
6. peace sign, index and middle finger up

Plain solid pure blue background (#007CFB) filling the whole image, no
shadows, no floor, no text, no labels, no numbers.
```

## Prompt 2 — Pose silang tangan

```
Edit the attached image. Keep the same boy exactly as he is: same head,
face, udeng, flower, hair, shirt, yellow sash, green sarong, legs, sandals,
same size, same position, same flat vector style and colors, and the same
plain solid blue background (#007CFB).

Change ONLY his arms: he now crosses his arms in front of his chest, white
long sleeves folded over each other at chest height, both hands visible
with chunky rounded cartoon fingers (a thumb and three fingers, skin color
#EFAB81) resting on the opposite upper arm. He looks a little impatient but
friendly.

Flat solid color blocks only, no gradients, no black outlines, no shading,
no text.
```

## Prompt 3 — Tangan menyatu (Om Swastiastu)

Versi pertama (2026-10-22) gagal: Gemini menggambar **karakter baru** (udeng cokelat, wajah lain, 3 kopi), bukan mengedit gambar Wayan. Kata "Balinese" dan "Om Swastiastu" menarik ke gambaran stok anak Bali, dan instruksi yang panjang membuat Gemini menganggapnya permintaan gambar baru. Versi 2 di bawah: instruksi edit pendek, gestur dijelaskan tanpa kata "Bali", satu karakter.

Cara pakai:
1. Paling aman: lanjutkan di **chat Gemini yang sama** dengan gambar silang tangan (yang berhasil), lalu lampirkan lagi `references/wayan-gemini-blue-original.jpeg`
2. Pastikan gambar benar-benar terlampir (muncul sebagai thumbnail) sebelum kirim

```
Edit this exact image. Do not redraw the character and do not add more
characters. Keep everything identical: face, eyes, udeng, flower, hair,
shirt, sash, sarong, legs, sandals, size, position, colors and the blue
background.

Change only his arms: both palms pressed flat together in front of the
middle of his chest, fingers pointing up, elbows bent out to the sides,
like a polite greeting. White sleeves, same skin color hands, flat style,
no outlines.
```

## Kenapa tiap bagian ada

| Bagian prompt | Alasan |
|---|---|
| Lampirkan gambar Wayan | Supaya gaya, warna kulit, dan ketebalan bentuk sama persis dengan tubuh yang sudah di-rig |
| `RIGHT hands` saja | Tangan kiri cukup dicerminkan di Rive. Setengah pekerjaan, setengah risiko gaya tidak konsisten |
| `thumb and three ... fingers` | Gaya kartun klasik. Lima jari di tangan sekecil ini jadi ramai dan path-nya membengkak |
| Warna `#EFAB81` / `#D69067` | Diambil dari path wajah dan hidung di Rive, jadi tangan langsung serasi |
| `no black outlines` | Wayan tidak punya garis tepi. Garis hitam juga menambah path |
| `short straight wrist stub, no sleeve` | Pangkal tangan diselipkan di bawah ujung lengan baju, jadi lengan baju tetap milik rig |
| `none touching`, grid, `same size` | Saat vectorize tiap tangan jadi path terpisah dan mudah dipotong satu-satu |
| Latar biru `#007CFB` | Sama seperti master. Warna ini tidak ada di tubuh Wayan, jadi aman dibuang setelah vectorize |
| Prompt 2 & 3 berupa **edit** gambar asli | Kepala dan kaki tetap identik, jadi posisi lengan langsung pas di atas rig tanpa perlu disesuaikan |
| Prompt 3: `same big round friendly eyes` | Di prompt 2 Gemini mengubah mata jadi kotak dan sinis. Wajahnya memang tidak dipakai, tapi wajah yang tetap sama biasanya ikut menjaga kepala dan badan tidak bergeser |
| Prompt 3: `thumb and four ... fingers` | Menyamakan dengan hasil lembar tangan, yang ternyata keluar 4 jari + jempol |
| Prompt 3: `must not cover his chin or the yellow sash` | Tangan harus pas di dada saja, supaya kepala dan sabuk dari rig tidak tertutup saat pose ditukar |

## Setelah Rozi generate

1. Simpan hasilnya, kirim path file ke chat
2. Aku cek: latar benar-benar biru polos, warna kulit tidak mendekati biru, tangan tidak saling menempel
3. Aku tunjukkan biaya vectorize, **tunggu OK**, baru vectorize
4. Hasil: `assets/vector/hands.svg`, `assets/vector/arms_crossed.svg`, dan (gambar 3) `assets/vector/hands_together.svg`

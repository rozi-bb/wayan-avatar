# Prompt Fase 1 — Konsep Wayan

Dipakai untuk generate 3 kandidat konsep. Edit file ini kalau mau ubah, lalu minta generate ulang.

## Parameter

| Field | Nilai |
|---|---|
| `model` | `recraftv4_1_vector` |
| `n` | 3 |
| `size` | `2:3` (potret, cocok untuk full body berdiri) |
| `controls.colors` | `247,181,41` · `124,179,66` · `240,205,170` · `30,30,30` |
| Biaya | **$0.24** |

## Prompt

```
Full body front-facing chibi mascot character, Balinese Indonesian boy,
chunky stylized proportions with an oversized round head about one third
of total height, short stubby rounded limbs, thick simple forms.

Wearing a white Balinese udeng headband tied in a knot at the front,
black hair, a yellow marigold flower tucked behind one ear, a plain white
long-sleeve shirt, a wide yellow sash at the waist, and a green sarong.

Large simple oval eyes, friendly closed smile, soft blush cheeks.

Flat vector illustration, bold saturated flat color blocks, no gradients,
no outlines, no fabric fold lines, minimal geometric shapes, strong
readable silhouette, plain white background, centered, standing straight
and symmetrical with arms relaxed at the sides, a clear gap between the
arms and the torso, feet apart.
```

## Kenapa tiap bagian ada

| Bagian prompt | Alasan |
|---|---|
| `chibi`, `oversized round head about one third of total height` | Inti gaya Duolingo. Tanpa angka eksplisit, Recraft cenderung balik ke proporsi normal |
| `short stubby rounded limbs, thick simple forms` | Mencegah pergelangan tangan tipis yang mustahil di-rig |
| udeng, bunga, baju putih, selendang kuning, kamen hijau | Identitas karakter dari referensi |
| `large simple oval eyes` | Mata besar sederhana lebih gampang diganti dan dianimasikan |
| `friendly closed smile` | Ini cuma penampung. Mulutnya akan **dilepas** dan diganti 14 bentuk viseme di Rive |
| `flat color blocks, no gradients, no outlines` | Menekan jumlah path. Gradasi dan outline bikin SVG membengkak |
| `no fabric fold lines` | Lipatan kain di referensi itu sumber path sampah terbesar |
| `strong readable silhouette` | Avatar akan tampil kecil di layar; siluet harus terbaca |
| `plain white background` | Background ditunda ke v2, dan latar polos bikin pemisahan bagian lebih gampang |
| `standing straight and symmetrical` | Simetris mempermudah duplikasi lengan/kaki kiri-kanan saat rigging |
| **`clear gap between the arms and the torso`** | **Paling penting untuk Fase 2.** Kalau lengan menempel di badan, path-nya menyatu dan lengan tidak bisa dipisah jadi aset sendiri |
| `feet apart` | Supaya kaki kiri dan kanan jadi dua bentuk terpisah, bukan satu gumpalan |

## Yang sengaja TIDAK dipakai

| Hal | Alasan |
|---|---|
| `style_reference_urls` ke gambar Vecteezy | Akan menarik hasil ke gaya Vecteezy, padahal kita justru mau meninggalkannya |
| Pose sembah (tangan menyatu di depan) | Lengan jadi tidak bisa dipisah untuk rigging |
| `random_seed` | Dibiarkan acak dulu supaya 3 kandidat benar-benar berbeda. Seed baru dikunci setelah ada yang disukai |
| Warna putih di `controls.colors` | Putih sudah jadi warna latar; menyebutkannya berisiko bikin baju lebur dengan background |

## Setelah generate

1. Rozi pilih satu dari tiga
2. Periksa jumlah path — target di bawah ~30
3. Kalau perlu, perbaiki prompt dan generate master final dengan `--seed` terkunci
4. Simpan sebagai `assets/vector/wayan_master.svg`

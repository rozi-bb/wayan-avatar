# Prompt: kepala menoleh 3/4

Dipakai di **aplikasi Gemini (gratis)** dan dikerjakan Rozi. Hasilnya lalu dipotong dan di-vectorize lewat Recraft (`scripts/recraft.py vectorize`, $0.01 per gambar, **izin dulu**), dan latar birunya dibuang dengan `scripts/strip_bg.py`. Jalurnya sama dengan master Wayan.

Recraft sudah dicoba tiga kali dan gagal ($0.22). Inpaint V3 dan image-to-image V4.1 sama-sama menggambar anak lain, karena memutar kepala adalah perubahan bentuk besar dan modelnya tidak menjaga identitas karakter.

| # | Isi | Lampirkan di Gemini |
|---|---|---|
| 1 | Kepala menoleh 3/4 ke **kiri gambar** | `references/wayan-gemini-blue-original.png` |
| 2 | Kepala menoleh 3/4 ke **kanan gambar** | `references/wayan-gemini-blue-original.png` |

Satu gambar per chat, dan tiap chat dimulai dengan gambar asli (bukan hasil sebelumnya), supaya kesalahan tidak menumpuk. Badan harus tetap sama persis dan di posisi yang sama, karena hanya kepalanya yang diambil, lalu ditukar di rig pada frame tercepat (seperti salam).

## Prompt 1: menoleh ke kiri gambar

```
Edit the attached image. This is the same boy, keep him exactly as he is:
same body, white shirt, yellow sash, green sarong, legs and sandals, same
size, same position in the picture, same flat vector style and colors, and
the same plain solid blue background (#007CFB).

Change ONLY his head: turn it about 30 degrees into a three-quarter view
toward the LEFT side of the picture, as if he is looking at something on
the left. Keep it the same head, just rotated:
- same round head shape and size, same skin color (#EFAB81)
- same face: big white eyes with dark round pupils looking left, small
  rounded nose, the same simple smile; the nose now points left and the
  eyes and mouth sit to the left of the face
- same white udeng head wrap with the same knot and folds; the front knot
  turns left with the face, so we see more of the udeng's right side
- his left ear (on the right side of the picture) and the yellow flower
  with an orange centre above it are now more visible, moved a little
  toward the middle of the head; his other ear is mostly hidden
- same dark hair showing under the udeng at the back

Flat solid color blocks only, no gradients, no black outlines, no shading,
no blush, no text. Do not change his age, face style or proportions.
```

## Prompt 2: menoleh ke kanan gambar

```
Edit the attached image. This is the same boy, keep him exactly as he is:
same body, white shirt, yellow sash, green sarong, legs and sandals, same
size, same position in the picture, same flat vector style and colors, and
the same plain solid blue background (#007CFB).

Change ONLY his head: turn it about 30 degrees into a three-quarter view
toward the RIGHT side of the picture, as if he is looking at something on
the right. Keep it the same head, just rotated:
- same round head shape and size, same skin color (#EFAB81)
- same face: big white eyes with dark round pupils looking right, small
  rounded nose, the same simple smile; the nose now points right and the
  eyes and mouth sit to the right of the face
- same white udeng head wrap with the same knot and folds; the front knot
  turns right with the face, so we see more of the udeng's left side
- his right ear (on the left side of the picture) is now more visible,
  with a little more dark hair behind it
- the yellow flower with an orange centre stays above his left ear, which
  is now toward the back of the head on the right edge, partly hidden
  behind the head

Flat solid color blocks only, no gradients, no black outlines, no shading,
no blush, no text. Do not change his age, face style or proportions.
```

## Kalau hasilnya melenceng

Kirim ini di chat yang sama, lalu ulangi:

- Kepala kurang menoleh: `Turn the head further, a clear three-quarter view, about 35 degrees.`
- Wajah atau gaya berubah: `Keep his face exactly like the original picture: same eyes, nose, smile and flat style. Only the angle of the head changes.`
- Badan ikut berubah: `Do not change anything below the neck; the body must match the original picture exactly.`

## Gambar tengah (sekitar 15°) untuk morph

Toleh dibuat mulus dengan morph: setiap bentuk kepala bergeser titik demi titik dari gambar lurus ke gambar 3/4 (`scripts/turn_morph.py`). Tanpa acuan di tengah, puncak udeng jadi rata dan rambut kelihatan di kedua sisi atas. Gambar tengah dipakai sebagai kunci ketiga: lurus → tengah → 3/4.

Satu chat per gambar, mulai dari gambar asli `references/wayan-gemini-blue-original.png`, lalu lampirkan juga hasil 3/4 sisi yang sama sebagai contoh arah (`references/wayan-head34-right-blue-original.jpeg` atau `...-left-...`).

### Tengah, menoleh ke kanan gambar

```
Edit the first attached image (the boy looking straight ahead). The second
image shows the same boy with his head turned about 30 degrees to the right.
Draw the in-between pose: keep everything exactly as in the first image
(same body, clothes, size, position, flat vector style, colors and plain
solid blue background #007CFB) and turn ONLY his head about 15 degrees
toward the RIGHT side of the picture, exactly halfway between the two
images:
- same round head shape and size, same skin color
- the face, nose and eyes have moved a little to the right, halfway
- the white udeng and its front knot have turned halfway to the right;
  the tall rounded top of the udeng sits near the middle of his head
- the dark hair shows a little at the back, on the left of the udeng
- the yellow flower with an orange centre above his left ear has moved a
  little toward the back of the head, still mostly visible
- his right ear (on the left of the picture) shows a bit more

Flat solid color blocks only, no gradients, no black outlines, no shading,
no blush, no text. Do not change his age, face style or proportions.
```

### Tengah, menoleh ke kiri gambar

```
Edit the first attached image (the boy looking straight ahead). The second
image shows the same boy with his head turned about 30 degrees to the left.
Draw the in-between pose: keep everything exactly as in the first image
(same body, clothes, size, position, flat vector style, colors and plain
solid blue background #007CFB) and turn ONLY his head about 15 degrees
toward the LEFT side of the picture, exactly halfway between the two
images:
- same round head shape and size, same skin color
- the face, nose and eyes have moved a little to the left, halfway
- the white udeng and its front knot have turned halfway to the left
- the dark hair shows a little more at the back, on the right of the udeng
- the yellow flower with an orange centre above his left ear (on the right
  of the picture) has moved a little toward the middle, more visible
- his other ear is a little more hidden

Flat solid color blocks only, no gradients, no black outlines, no shading,
no blush, no text. Do not change his age, face style or proportions.
```

## Lembar putar kepala (flipbook), dipakai sekarang

Morph dari dua gambar tetap kurang mulus, karena bentuk di tengahnya hasil tebakan. Cara yang dipakai: banyak gambar per sudut, ditukar cepat seperti flipbook. Mata, alis, dan mulut rig tetap meluncur mulus di atasnya.

**Kenapa satu lembar, bukan satu gambar per chat:** Gemini menjaga gaya, udeng, dan bunga tetap sama di dalam satu gambar. Kalau tiap sudut digenerate terpisah, detailnya bergeser sedikit dan animasinya akan "bergetar".

**Jumlah:** 5 kepala per sisi (0°, 7,5°, 15°, 22,5°, 30°). Toleh berlangsung sekitar 10 frame, jadi tiap gambar tampil kira-kira 2 frame, setara animasi 30 fps.

**Cara:** lanjutkan di chat Gemini tempat kedua kepala 3/4 dibuat (kiri dan kanan ada di chat yang sama), jadi tidak perlu melampirkan apa pun lagi. Gemini sudah punya gambar asli dan kedua hasil 30°-nya, dan gambar-gambar itu dipakai sebagai ujung awal dan akhir lembar. Kirim Prompt A dulu, lalu Prompt B.

### Prompt A: menoleh ke kanan gambar (kirim dulu)

```
The two turned heads you drew in this chat are perfect. Now I need the
in-between angles for a smooth animation, starting with the right side. Draw a head turnaround sheet of this same boy: FIVE heads in
one horizontal row, all the same size, evenly spaced, not touching or
overlapping, each about as big as in the pictures above.

From left to right the head turns toward the RIGHT side of the picture in
equal steps:
1. 0 degrees: exactly like the original picture, looking straight ahead
2. 7.5 degrees
3. 15 degrees
4. 22.5 degrees
5. 30 degrees: exactly like the head turned to the RIGHT that you drew
   earlier in this chat
Each step is a small, even change from the one before it, like frames of
a smooth animation.

Keep every detail identical on all five heads, only the angle changes:
same round head shape and size, same skin color, same big white eyes with
dark round pupils, same simple smile, same white udeng with its front knot
and folds, same dark hair, same yellow flower with an orange centre above
his left ear. As the head turns right, the face, nose, eyes and the udeng
knot move to the right step by step, his right ear (left of the picture)
and the hair behind it show a little more each step, and the flower moves
toward the back of the head until it is partly hidden as in head 5.

Draw only the heads with a short neck stub, no body, all on the same
baseline. Flat solid color blocks only, no gradients, no black outlines,
no shading, no blush, no text, no numbers. Plain solid blue background
(#007CFB).
```

### Prompt B: menoleh ke kiri gambar (sesudah A, di chat yang sama)

```
Great. Now the same sheet for the left side. Draw a head turnaround
sheet of this same boy: FIVE heads in
one horizontal row, all the same size, evenly spaced, not touching or
overlapping, same size, spacing and baseline as the right-side sheet.

From left to right the head turns toward the LEFT side of the picture in
equal steps:
1. 0 degrees: exactly like the original picture, looking straight ahead
2. 7.5 degrees
3. 15 degrees
4. 22.5 degrees
5. 30 degrees: exactly like the head turned to the LEFT that you drew
   earlier in this chat
Each step is a small, even change from the one before it, like frames of
a smooth animation.

Keep every detail identical on all five heads, only the angle changes:
same round head shape and size, same skin color, same big white eyes with
dark round pupils, same simple smile, same white udeng with its front knot
and folds, same dark hair, same yellow flower with an orange centre above
his left ear. As the head turns left, the face, nose, eyes and the udeng
knot move to the left step by step, the flower (right of the picture)
comes toward the front and shows a little more each step, his left ear
and the hair behind it show more on the right, and his other ear gets
hidden as in head 5.

Draw only the heads with a short neck stub, no body, all on the same
baseline. Flat solid color blocks only, no gradients, no black outlines,
no shading, no blush, no text, no numbers. Plain solid blue background
(#007CFB).
```

### Kalau hasilnya melenceng

- Langkahnya tidak rata: `Make the five steps equal: each head turns the same small amount more than the one before.`
- Ukuran atau tinggi kepala berbeda: `All five heads must be exactly the same size and sit on the same baseline.`
- Kepala pertama atau terakhir beda: `Head 1 must look exactly like the original picture and head 5 exactly like the turned head you drew earlier for this side.`
- Detail berubah antar kepala: `Keep the udeng, knot, flower, hair and face identical on every head; only the angle changes.`

Biaya setelahnya: vectorize 8 kepala (sudut 0° tidak dipakai karena rig sudah punya), sekitar **$0.08**, izin dulu.

## Lembar putar kepala lewat ChatGPT (Gemini gagal)

Lembar dari Gemini hasilnya jelek. Dipindah ke ChatGPT, dengan lampiran dua gambar 3/4 (urutannya penting):

1. `references/wayan-head34-left-blue-original.jpeg`: menoleh ke kiri gambar
2. `references/wayan-head34-right-blue-original.jpeg`: menoleh ke kanan gambar

Satu gambar berisi dua baris, supaya semua sudut digambar sekaligus dan konsisten.

```
Image 1 and Image 2 show the same cartoon boy. In Image 1 his head is
turned about 30 degrees toward the LEFT side of the picture. In Image 2
his head is turned about 30 degrees toward the RIGHT side of the picture.

Make ONE landscape image (3:2) that is a head turnaround sheet of this
exact boy, for a smooth head-turn animation. Two rows, five heads per
row, all heads the same size, evenly spaced, not touching, every head on
the same baseline within its row:

Top row, turning LEFT, from left to right:
  0 degrees (looking straight at the viewer), 7.5, 15, 22.5, 30 degrees
  (the last head must match Image 1 exactly)
Bottom row, turning RIGHT, from left to right:
  0 degrees (looking straight at the viewer), 7.5, 15, 22.5, 30 degrees
  (the last head must match Image 2 exactly)

The 0-degree heads are the halfway point between Image 1 and Image 2:
face centred, both ears showing the same, the udeng knot in the middle,
the yellow flower above his left ear (right side of the picture) half
visible. Each step is a small, equal change from the one before it,
like frames of an animation.

Copy everything from the two images exactly; only the angle of the head
changes: same round head shape and size, same skin color, same big white
eyes with dark round pupils, same small nose, same simple smile, same
white udeng head wrap with the same knot and folds, same dark hair, same
yellow flower with an orange centre, same ears.

Draw only the heads with a short neck stub, no body. Same flat vector
style as the images: flat solid color blocks only, no gradients, no
outlines, no shading, no blush, no text, no numbers, no labels. Plain
solid blue background (#007CFB) filling the whole image.
```

Kalau melenceng, kirim di chat yang sama:
- `Keep every head identical to Image 1 and Image 2 in style and details; only the angle changes.`
- `Make all ten heads exactly the same size and evenly spaced.`
- `Make the steps equal: each head turns the same small amount more than the one before.`

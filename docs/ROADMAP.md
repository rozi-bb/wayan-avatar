# Roadmap — Wayan, Avatar AI

Urutan pengerjaan dari nol sampai avatar bisa bicara online.
Detail produk: [PRD.md](PRD.md)

**v1 = Fase 0–5, 5b, lalu 7.** Teks diketik manual, belum ada LLM.
**v2 = Fase 6.** Percakapan suara + DeepSeek, dikerjakan setelah v1 bagus.

**Aturan:** satu fase per giliran. Tidak ada panggilan Recraft tanpa izin Rozi, dan biayanya selalu ditunjukkan lebih dulu.

---

## Fase 0 — Fondasi ✅

- [x] Riset jalur Recraft (MCP vs REST API)
- [x] Pasang skill `recraft-api`
- [x] `scripts/recraft.py` — `balance` / `gen` / `vectorize` / `style` + `--dry-run`
- [x] `.env` + `.gitignore`
- [x] Uji endpoint: saldo, generate, vectorize
- [x] PRD & roadmap

Terpakai: $0.104. Sisa: **$4.90**

---

## Fase 1 — Desain karakter ✅

Hasil: `assets/vector/wayan_master.svg` — full body, 42 path, 11 warna datar, latar transparan.

- [x] Generate 3 kandidat konsep di Recraft (`recraftv4_1_vector`) — $0.24. **Ditolak:** kalah jauh dari referensi; 2 dari 3 kehilangan baju putih
- [x] Ganti jalur: generate di **app Gemini gratis** pakai referensi Vecteezy + prompt gaya Duolingo
- [x] Vectorize v1 — $0.01. **Gagal:** baju putih lebur ke latar putih
- [x] Minta Gemini ganti latar ke **biru `#007CFB`** (warna yang tidak ada di tubuh Wayan)
- [x] Crop ke badan → vectorize v2 — $0.01
- [x] Hapus path latar biru (`scripts/strip_bg.py`) → master transparan
- [x] Periksa: tangan, kaki, mata, mulut terpisah ✅ · tepi mulus saat zoom 5× ✅

Terpakai: **$0.26**

### Alur yang terbukti untuk aset berikutnya

```
app Gemini (latar biru polos) → crop → Recraft /vectorize ($0.01) → strip_bg.py
```

Aturan warna latar: **tidak boleh ada di tubuh karakter.** Putih bertabrakan dengan baju & udeng, hijau dengan kamen. Pakai biru atau magenta.

---

## Fase 2 — Pisah bagian & rigging di Rive

Tujuan: master jadi bagian-bagian yang bisa digerakkan.

File Rive: **`wayan`** (id 2669702), artboard **Wayan** 600×900. Jangan sentuh tab `avatar-ai` dan `Untitled`.

- [x] Impor master SVG ke Rive lewat MCP (upload via data URI, editor di-sandbox macOS)
- [x] Skala node `Wayan` 38,086% → tinggi 780, posisi (43.5, 60)
- [x] Beri nama 42 bentuk. `_L` = kiri Wayan = **kanan layar**
- [x] Susun hierarki `Wayan > Head, Body, Leg_R, Leg_L` (Head paling depan) + grup `Eye_L`, `Eye_R`, `Kamen_Group`
- [x] Pindahkan pivot: **Head → leher** (690, 990), **Body → pinggang** (680, 1290) dalam koordinat SVG. Dites: kepala miring 12° berayun dari leher ✅
- [x] ~~Potong baju di bahu~~ → **diganti skinning**: baju tetap satu path, lengan baju melengkung ikut bones (gaya rubber-hose Duolingo, tanpa sambungan di bahu)
- [x] Panduan bones: [panduan-bone.svg](panduan-bone.svg)
- [x] **Rozi bikin 5 bones** di editor Rive: Spine, UpperArm_R/Forearm_R, UpperArm_L/Forearm_L
- [x] Pindahkan bones ke dalam `Body` (skala dinormalkan ke 100%, panjang ×2,6256) → ikut memantul bersama badan
- [x] Ikat path `Shirt` ke 5 bones. **Auto-weight ditolak:** kerah ikut lengan (bikin celah gelap di leher) + bobot silang ke lengan seberang
- [x] **Bobot ditulis manual** untuk 45 titik: kerah & badan = Spine 100%, bahu/ketiak = 50/50, siku = 40/60, manset = Forearm
- [x] Tangan ditempel ke Forearm; bones lengan dipindah ke depan supaya tangan tidak tertutup baju
- [x] Tambah `Neck_Back` (elips kulit gelap di belakang baju) → tidak ada lubang saat kepala miring
- [x] Tes pose: lengan terangkat, badan naik 30, kepala miring 8° ✅ · posisi diam identik dengan master ✅
- [ ] Alis belum ada di master → gambar di Rive (Fase 3)
- [ ] Kaki: tanpa bones di v1, digerakkan sebagai grup kaku

Catatan untuk animasi: **lambaian** = lengan atas ke samping (±−10°), lengan bawah tegak. Kalau lengan atas diarahkan ke atas, tangan berakhir di belakang kepala.
- [ ] ViewModel `FaceVM`: `visemeId`, `lookX`, `lookY`, `expression`, `convState`

Biaya Recraft: **$0**

**Gerbang:** butuh kerja manual Rozi di editor Rive. Siapkan waktu khusus.

---

## Fase 3 — Bentuk mulut & ekspresi

Tujuan: 16 bentuk mulut + aset ekspresi, semua sejajar sempurna.

- [x] Gambar **16 bentuk mulut** langsung di Rive, acuan `Referensi Viseme Azure` di vault
  `Rest AH AH_Clean AA AA_Clean OH EH ER EE OO KG DT SS SH FV MBP`
  - Satu titik pusat bersama: grup `Mouth` (origin = tengah senyum diam) → tidak ada mulut yang "loncat"
  - Palet: rongga `#4a1f1c`, lidah `#e8737a`, gigi `#fdfdfc`, bibir `#d69067`
  - AH & KG = salinan AA yang diskalakan; 9 lainnya digambar dari templat bentuk-D yang sama (script)
  - QC 22 viseme vs gambar Azure: [assets/preview/mouth/qc22.html](../assets/preview/mouth/qc22.html)
- [x] Revisi Rozi: ID 8 & 9 **tanpa gigi** (`AH_Clean`, `AA_Clean`), ID 18 FV **gigi menutup seluruh bukaan**. ID 1, 2, 11 tetap bergigi. Sisanya disetujui.

Peta final viseme → mulut (dipakai kode web di Fase 5):

```js
// index = Azure viseme ID (0–21), value = grup Mouth_* di Rive
const MOUTH = ['Rest','AH','AA','OH','EH','ER','EE','OO','AH_Clean','AA_Clean','OH',
               'AA','KG','OH','DT','SS','SH','DT','FV','DT','KG','MBP'];
```
- [x] Semua di grup `Mouth`, tiap viseme = grup `Mouth_*`, dinyalakan lewat opacity (Solo tidak tersedia lewat MCP)
- [x] Varian mata: terbuka (`Eye_L/R`, sudah ada) + merem senyum `^ ^` (`EyeHappy_L/R`, baru)
- [x] Alis `Brow_L/R` — baru, warna `#3f3e3f`, diletakkan **di belakang udeng** (tepat di depan `Face`) supaya saat naik terselip ke balik ikat kepala
- [x] Mulut ekspresi: ketawa = `Mouth_AA`; sedih = `Mouth_Sad` (senyum diam dibalik vertikal)
- [x] Pratinjau 5 ekspresi: [assets/preview/expr/index.html](../assets/preview/expr/index.html)

Resep ekspresi (dipakai jadi animasi `E_*` di Fase 4; koordinat dalam ruang `Head`):

| Ekspresi | Mata | Pupil | Alis (y, rotasi R / L) | Mulut |
|---|---|---|---|---|
| Netral | `Eye_*` 100% | 100% | −482, 0° / 0° | `Mouth_Rest` |
| Senyum | `EyeHappy_*` | — | −494, 0° | `Mouth_Rest` |
| Kaget | `Eye_*` 112%, mata putih diganti `EyeRound_*` (bulat penuh, tanpa lekukan pipi) | 70% | −506, 0° | `Mouth_OH` |
| Sedih | `Eye_*` skalaY 86% | turun ke y 14 | −478, −14° / +14° | `Mouth_Sad` |
| Ketawa | `EyeHappy_*` | — | −498, 0° | `Mouth_AA` |

Kedip = skalaY `Eye_*` ke ±10%, tidak perlu aset terpisah.

Biaya Recraft: **$0** — ini penghematan terbesarnya (hemat ~$1.28 dibanding digenerate)

---

## Fase 4 — Animasi

Tujuan: Wayan terasa hidup walau diam.

ViewModel **`FaceVM`** (instance diikat ke artboard): `visemeId` 0–21, `expression` 0–4, `lookX`/`lookY` −1..1, `talking` boolean.

- [x] **Mulut lewat data binding, bukan state machine.** Opacity tiap grup `Mouth_*` diikat ke `visemeId` lewat converter rumus
  `max(0, 1 − (v − N)²) × 100` (dijumlah untuk mulut multi-ID). `Mouth_Rest`/`Mouth_Sad` juga membaca `{{FaceVM/expression}}` → saat diam & sedih tampil cemberut. Menggantikan 16 animasi `V_*` + 22 transisi di catatan vault
- [x] Mata ikut cursor: x/y `Pupil_L/R` diikat ke `lookX`/`lookY` (±30 / ±25)
- [x] `Idle` — napas 2 s loop: Body skalaY 102,5% dari pinggang, kepala naik 10, lengan sedikit terbuka
- [x] `Blink` — 4 s loop, grup `Blink_L/R` (di dalam `Eye_L/R`) skalaY → 10%. Grup terpisah supaya tidak bentrok dengan skala mata dari ekspresi
- [x] `E_Netral/Senyum/Kaget/Sedih/Ketawa` — pose dari tabel resep, 18 properti sama di semua pose (termasuk opacity `EyeWhite_*`/`EyeRound_*`), blend 200 ms
- [x] `Talk` — 0,5 s loop: kepala ±2,5° + squash/stretch, dipicu `talking` (bukan `visemeId`, karena nilainya kembali 0 di sela kata)
- [x] State machine `State Machine 1`, layer: **Idle** · **Blink** · **Expression** (Any State → `E_*` saat `expression == n`) · **Talk** (Talk_Rest ⇄ Talk, 150 ms)
- [x] Export `web/wayan.riv` lewat `scripts/export_riv.sh`
- [x] Diuji di runtime web (`@rive-app/canvas@2.44.0`): 22 viseme, mulut sedih, arah pandang, 5 ekspresi, Talk, Blink — [web/preview.html](../web/preview.html)

Catatan:
- Editor Rive **tidak menjalankan data binding** di mode desain dan simulasi state machine ditolak di mode Animate → selalu uji lewat `web/preview.html`
- Akun Rive Free: splash hitam ±3 detik di awal
- Kaget terlihat halus di kanvas kecil — kandidat dipertegas setelah ditinjau

Biaya Recraft: **$0**

---

## Fase 5 — Web & TTS ← **akhir v1**

Tujuan: Wayan bicara di browser dari teks yang diketik, mulut sinkron.

- [x] Backend `server.py` (stdlib): sajikan `web/` + `GET /api/speech-token` (key tetap di server, token di-cache 8 menit). Jalankan: `PORT=8766 python3 server.py` — **port 8765 dipakai server project lama**
- [x] `web/index.html`: Wayan + nama suara + pilihan suara + kotak teks (maks 400 karakter) + Speak/Stop + petunjuk tag
- [x] Artboard Rive dibuat transparan → Wayan tampil di latar halaman
- [x] Azure Speech SDK `1.52.0` (browser): `visemeReceived` + `wordBoundary`, posisi audio dari `SpeakerAudioDestination`
- [x] Viseme → `visemeId` langsung (data binding mulut sudah memetakan ke 16 bentuk)
- [x] Parser tag: tag dicocokkan ke `wordBoundary.textOffset` kata sesudahnya. Suara HD Inggris ikut berekspresi lewat penanda `[happy]` `[surprised]` `[sad]`; `[ketawa]` → `[laughter]` (semua bahasa HD) + mata `^ ^` + mulut memantul selama jeda tawa. Diuji tanpa audio: posisi tag, escape `&`/`<`, tag asing dibuang
- [x] Key Azure disalin dari `.env` project lama atas izin Rozi (region `southeastasia`)
- [x] **Diuji dengan audio sungguhan**: kelima kandidat mengirim viseme (24–82 per kalimat, 11–18 bentuk berbeda)
- [x] Tag dijadwalkan lewat posisi kata. Perbaikan dari uji nyata: kata sesudah penanda emosi HD dilaporkan di awal penandanya → cari dari posisi tag, bukan sesudah penanda; tag di awal teks langsung aktif (kata pertama bisa ber-offset −1)
- [x] **Ardi HD (id-ID) hampir tidak mengirim posisi kata** → cadangan: perkiraan proporsional dari posisi tag di teks (tanpa durasi tawa) lalu ditempel ke jeda diam terdekat di aliran viseme. Hasil uji: `[kaget]` tepat sebelum "Wah", `[ketawa]` tepat selama tawa
- [x] Sesudah tawa wajah kembali **senyum** (bukan ekspresi sebelumnya)
- [ ] Pilih suara final (dengar langsung). Kandidat di halaman: Andrew HD, Goldenspark HD Omni, Jason+pitch (Inggris); Ardi HD, Ardi+pitch (Indonesia)
- [ ] Putuskan bahasa: PRD bilang Inggris, contoh Rozi berbahasa Indonesia
- [ ] Halaman QC: 22 viseme, mulut kita vs gambar acuan Azure
- [ ] Uji pakai 9 kalimat tes dari vault
- [ ] Pembatas panjang teks

**Gerbang:** lipsync harus pas dan ekspresi harus jalan sebelum lanjut ke Fase 7.

---

## Fase 5b — Idle hidup ala Duolingo

Tujuan: saat diam, Wayan terasa hidup dan punya kepribadian (ceria, enerjik, anak Bali), dengan gerakan halus ala Duolingo. Daftar gerakan disepakati dengan Rozi 2026-10-22.

### Daftar gerakan

| # | Gerakan | Kapan | Isi |
|---|---|---|---|
| 1 | Napas & kedip | selalu | Sudah ada (`Idle`, `Blink`) |
| 2 | Lirikan mata | selalu | Sudah ada (halaman web, saat kursor diam/keluar) |
| 3 | **Kepala ikut lirikan** | selalu | Kepala miring ±4° dan bergeser searah `lookX` |
| 4 | **Badan bergoyang** | selalu | Berat badan pindah kiri-kanan, ±1°, siklus ±6 s |
| 5 | **Om Swastiastu** | sekali, saat halaman dibuka | Kedua tangan menyatu di dada, kepala mengangguk, lalu senyum |
| 6 | **Udeng melorot** | acak | Udeng turun menutupi mata → didorong naik → tertawa kecil |
| 7 | **Kepal "Yes!"** | acak | Tangan mengepal ditarik ke bawah, senyum lebar |
| 8 | **Silang tangan** | bosan (±30 s tanpa interaksi) | Lengan bersilang, jari mengetuk, satu alis naik, lalu kembali |

Aturan:
- Aksi acak (6–7) bergantian tiap 10–18 detik, tidak sama dua kali berturut-turut
- Aksi hanya saat Wayan diam: tidak bicara, kursor tidak sedang digerakkan. Mulai bicara → aksi berhenti halus kembali ke pose normal
- Gerakan dari daftar lama (seledet, senandung, lambai, jempol + kedip) disimpan sebagai cadangan kalau 6–7 terasa monoton

### Prinsip gerak (berlaku untuk semua aksi)

- **Ancang-ancang**: gerak kecil ke arah berlawanan dulu (100–150 ms)
- **Lewat lalu memantul**: easing cubic dengan overshoot, bukan linear
- **Kepala memimpin, badan menyusul** 2–3 frame kemudian
- **Bunga & ujung udeng ikut bergoyang** telat sesudah kepala berhenti
- **Kedip saat menoleh**
- **Tukar bentuk tangan di tengah gerakan cepat** supaya pergantiannya tidak terlihat
- Tidak pernah diam total: napas + goyang tetap jalan di bawah aksi. Semua transisi 200–300 ms

### Aset

- [x] Prompt Gemini: [prompt-tangan.md](prompt-tangan.md)
- [x] `assets/vector/hands.svg` — 6 tangan kanan (telapak, jempol, telunjuk, kepal, telapak samping, peace), 18 path. Tangan kiri = cerminan di Rive
- [x] `assets/vector/arms_crossed.svg` — Wayan bersilang tangan, kanvas 1347×2048 sejajar master, 50 path. Yang dipakai: dada + lengan + sabuk
- [x] `assets/vector/hands_together.svg` — tangan menyatu (Om Swastiastu), kanvas sejajar master, 56 path. Gemini gagal 2× (menggambar anak Bali baru), jadi dibuat dengan **Recraft inpaint** (`recraftv3`): gambar master + mask lengan & dada (`references/mask-arms-chest.png`), hanya area mask yang digambar ulang. Kepala & kaki identik (selisih rata-rata 3/255). Variasi 1 dari 2 dipilih Rozi

### Pekerjaan

- [x] Kepala ikut lirikan, dua lapis: grup `HeadLook` (kepala utuh, pivot leher) miring `headX × 0,045 rad` (±2,6°) + geser kecil, dan grup `FaceFeatures` (mata, hidung, mulut) + alis bergeser `headX × 16` di dalam wajah → kesan menoleh ala Duolingo tanpa membuka celah di leher. `headX/headY` terpisah dari `lookX/lookY` supaya kepala bisa lebih lambat dari mata
- [x] Bahu baju disambung: `Shoulder_L/R` di belakang `Shirt`, garis bahu landai sampai leher. Sebelumnya tepi baju di bawah wajah melengkung turun, jadi saat kepala bergerak baju tampak terputus
- [x] Gerak mata ala manusia (halaman web): saccade 40–160 ms tergantung jarak (ease-out), pursuit halus saat mengikuti kursor, kepala menyusul lewat pegas teredam (±0,6 s), mata kembali 35% ke tengah setelah kepala menoleh, micro-saccade tiap 0,5–1,4 s saat menatap, kedip (`BlinkOnce`, trigger `blink`) di 60% lirikan besar. Lirikan idle diskalakan 60–100%, tahan 0,5–1,3 s, istirahat 1,8–4,5 s
- [x] Layer `Sway`: animasi `Sway` loop 6 s, `Body` miring ±1° dari pinggang + `Head` x 684,8 ↔ 695,2 mengikuti bahu (cubic ease-in-out)
- [x] Bentuk tangan: 6 pose × 2 lengan (`Hand_L/R_Open/Thumb/Point/Fist/Side/Peace`) anak tulang lengan bawah, dibuat dari `hands.svg` lewat `scripts/hands_to_rive.py` (tangan kiri = cerminan). Tangan bulat lama tetap tampil sebagai manset; pangkal pose dimulai di dalamnya sehingga menyatu
- [x] Grup `Udeng` (+ `Hair_Top`) di atas mata, di bawah bunga; `Hair_Cap` (warna rambut) di bawah udeng supaya kepala tidak botak saat udeng turun
- [x] Pose ganti badan: `Pose_Salam` & `Pose_Silang` (badan dari `hands_together.svg`/`arms_crossed.svg`, `scripts/pose_to_rive.py`, sejajar rig). Selama pose, baju/kamen/leher/tangan rig disembunyikan; lengan rig bergerak ke dada dulu supaya pergantian tidak terlihat
- [x] Animasi `A_Salam` (2 s, membungkuk), `A_Udeng` (1,7 s), `A_Yes` (1,5 s), `A_Silang` (3,2 s, alis naik + kepala miring) + `A_Rest`. Tangan pendorong udeng = salinan `HandPush` di dalam kepala (lengan asli tertutup kepala), posisinya dari forward kinematics lengan
- [x] Layer **Aksi**: `A_Rest` → `A_*` saat `action == n` (1 Salam, 2 Udeng, 3 Yes, 4 Silang), kembali saat `action == 0` (blend 200–250 ms)
- [x] Halaman web: salam sekali setelah splash Rive hilang (dideteksi dari piksel kanvas), Udeng/Yes bergantian tiap 10–18 s, silang setelah 30 s tanpa input; tidak mulai saat kursor bergerak, dibatalkan saat bicara. Ekspresi & mata ikut (kaget saat udeng jatuh, tawa sesudahnya, mulut "Yes!", lirik ke samping saat bosan)
- [x] Diuji di browser: keempat aksi tampil, salam 3× berturut-turut benar, aksi berhenti saat bicara dimulai
- [x] Revisi Rozi (2026-10-22): Salam memakai sabuk & kamen rig sendiri (pose hanya badan atas, dipotong di garis sabuk, `--upper`); isian bahu & leher belakang tetap tampil saat Salam/Silang; `Hair_Cap` mengikuti tepi kepala penuh + tepi gelap saat udeng turun, udeng miring −2°; "Yes!" memakai tekukan siku lebih ringan (naik 15°/−85°, tarik 30°/−72°) supaya lengan baju tidak cekung; tiap aksi mulai dari wajah netral
- [x] Om Swastiastu versi bone + tukar gambar (2026-10-23): lengan asli naik pakai bone (f0–f19, makin cepat), di f20 (333 ms) diganti `Pose_Salam` (K2, gambar tangan menyatu), badan memantul lalu menunduk, f90 balik ke bone dan turun ke default (2 s). Aksi lain (Udeng, Yes, Silang), `Pose_Silang` dan `HandPush` dihapus atas permintaan Rozi; layer Aksi tinggal `A_Rest` ↔ `A_Salam` (`action` = 1). Halaman web memutar salam sekali setelah splash Rive hilang (+600 ms, senyum saat menunduk) dan membatalkannya begitu `speak()` dipanggil; transisi keluar A_Salam → A_Rest 0 ms supaya pembatalan tidak menumpuk dua lapis transparan. Lembar frame: `assets/preview/salam_k1.html`. Diuji di browser: urutan benar, tidak ada error
- [x] Jempol 👍 (2026-10-23): `A_Jempol` (`action` = 2, 1,8 s). Lengan kanan naik pakai bone, di f15 tangan bulat diganti tangan jempol hasil Recraft V4.1 (`Hand_R_ThumbUp`, pivot di pergelangan, di balik manset) bersama siku bulat `ElbowThumb_R` dan garis lipatan lengan bawah; jempol memantul (lewat, balik, pop, goyang), badan memantul, kepala mengangguk, lalu turun dengan pergantian balik di f80. Dipicu tag `[jempol]`/`[thumbsup]` di teks (dengan senyum). `A_Rest` mengembalikan tangan, siku dan bahu supaya pembatalan bersih. Lembar frame: `assets/preview/jempol.html`. Keyframe: `scripts/jempol_keys.py`
- [x] Coba jempol lewat inpaint 2×4 ($0.32): sambungan bahu-lengan-tangan tidak natural, tidak dipakai. Tangan saja via generate V4.1 ($0.14) + vectorize ($0.01)
- [x] Background (2026-10-23): Recraft V4.1 vector, 2:3 seperti panggung. Pura pertama ditolak (gerbang tertutup Wayan), Pura B (gerbang di kiri-kanan) dan dua latar baru dibandingkan di `assets/preview/bg_compare.html`. Rozi memilih **rumah adat Bali** (`bg_rumah.svg`, angkul-angkul + bale) dengan langit krem diganti biru (edit SVG, bunga kamboja tetap putih) supaya udeng dan baju Wayan kontras. Wayan digambar 66% lebar panggung, berdiri 2% dari bawah (`--wayan`). Total background $0.56
- [x] Script: `scripts/salam_keys.py` (tulis ulang keyframe A_Salam, bisa dijalankan ulang) dan `scripts/rive_frames.py` (render frame timeline mana pun ke PNG untuk lembar review, lalu kembalikan pose diam)
- [x] Coba K1 (pose tengah) lewat Recraft inpaint 2× ($0.16): gagal, telapak selalu menempel. Diganti pose bone

**Gerbang:** Rozi menonton tiap aksi di browser dan setuju sebelum lanjut ke Fase 7.

Biaya Recraft: **$1.30** (background $0.56, jempol $0.47, percobaan K1 $0.16, sebelumnya $0.11) (vectorize tangan + silang tangan $0.02, inpaint 2 variasi $0.08, vectorize tangan menyatu $0.01).

---

## Fase 6 — Percakapan suara ⏸️ **ditunda ke v2**

Dikerjakan setelah v1 terbukti bagus. Format tag sudah disiapkan sama persis, jadi fase ini tinggal mengganti sumber teksnya saja.

- [ ] Izin mikrofon + push-to-talk (tahan tombol)
- [ ] Azure STT streaming
- [ ] DeepSeek: system prompt yang mewajibkan tag ekspresi
- [ ] Streaming jawaban → mulai bicara sebelum kalimat selesai
- [ ] **Nyela:** tekan tombol → audio berhenti, state machine reset, mulai merekam
- [ ] Animasi `C_*` — status dengerin & mikir
- [ ] Status tampil di wajah: diam → dengerin → mikir → ngomong
- [ ] Pembatas jumlah giliran per sesi

**Gerbang:** fase paling rawan. Uji tiap potong sebelum disambung.

---

## Fase 7 — Deploy v1

- [x] Repo GitHub **private**: [rozi-bb/wayan-avatar](https://github.com/rozi-bb/wayan-avatar)
- [x] Pastikan tidak ada key ter-commit (`.env` di-ignore, isi repo dipindai)
- [ ] Deploy dengan backend (key tetap di server)
- [ ] Uji di perangkat lain
- [ ] Tulis README

---

## Ringkasan biaya

| Fase | Recraft |
|---|---|
| 0 — Fondasi | $0.104 ✅ |
| 1 — Desain karakter | $0.26 ✅ |
| 2–4 — Rive | $0 |
| 5, 7 — Web & deploy | $0 |
| 5b — Idle hidup | $0.11 ✅ |
| 6 — Percakapan (v2) | $0 |
| **Total** | **±$0.61** |

Seluruh biaya Recraft habis di Fase 1. Sesudah itu tidak ada lagi pengeluaran aset.

Sisa saldo setelahnya: **±$4.40** — cukup longgar buat revisi desain kalau kandidat pertama kurang sreg, atau buat bikin background di v2.

Biaya Azure terpisah dan jalan terus selama dipakai. Perlu dibatasi sebelum dibuka online.

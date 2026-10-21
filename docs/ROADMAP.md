# Roadmap — Wayan, Avatar AI

Urutan pengerjaan dari nol sampai avatar bisa bicara online.
Detail produk: [PRD.md](PRD.md)

**v1 = Fase 0–5 lalu 7.** Teks diketik manual, belum ada LLM.
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

- [ ] Repo GitHub **private**
- [ ] Pastikan tidak ada key ter-commit
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
| 6 — Percakapan (v2) | $0 |
| **Total** | **±$0.50** |

Seluruh biaya Recraft habis di Fase 1. Sesudah itu tidak ada lagi pengeluaran aset.

Sisa saldo setelahnya: **±$4.40** — cukup longgar buat revisi desain kalau kandidat pertama kurang sreg, atau buat bikin background di v2.

Biaya Azure terpisah dan jalan terus selama dipakai. Perlu dibatasi sebelum dibuka online.

# PRD — Wayan, Avatar AI

Avatar animasi yang bisa bicara dengan mulut sinkron dan wajah berekspresi.

Dikerjakan dua tahap:

| | Isi | Masukan |
|---|---|---|
| **v1 — fokus sekarang** | Avatar, animasi, lipsync, ekspresi | **Teks diketik manual** |
| v2 — nanti | Percakapan suara + LLM | Mikrofon → STT → DeepSeek |

v1 harus benar-benar bagus dulu. Lapisan percakapan baru ditumpuk setelah lipsync-nya pas.

**Status:** perencanaan. Belum ada aset yang digenerate.
**Terakhir diperbarui:** 2026-10-21

---

## 1. Tujuan

Portfolio / demo teknis. Yang dipamerkan: pipeline lengkap dari aset AI → rig Rive → percakapan suara real-time.

Ukuran berhasil: orang yang membukanya bisa langsung ngobrol dengan Wayan tanpa membaca petunjuk, dan avatarnya terasa hidup — bukan gambar diam yang mulutnya komat-kamit.

Bukan tujuan: jadi produk komersial, melayani banyak user sekaligus, atau mendukung banyak karakter.

---

## 2. Karakter

| Field | Keputusan |
|---|---|
| Nama | **Wayan** |
| Bentuk | Anak laki-laki Bali |
| Kepribadian | Ceria & enerjik |
| Gaya bicara | Santai, ramah, bahasa Inggris |
| Bahasa | **Inggris saja** |
| Gaya gambar | Flat vector, ala Duolingo |
| Bagian tubuh | **Full body** |
| Background | Ditunda ke v2 (hemat biaya) |

### Ciri visual yang dipertahankan

Dari referensi `references/ref-bali-vecteezy.jpg`:

- Udeng putih bersimpul di depan
- Rambut hitam
- Bunga marigold kuning di telinga
- Baju putih lengan panjang
- Selendang kuning di pinggang
- Kamen hijau

### Yang diubah jadi ala Duolingo

| Aspek | Referensi | Target |
|---|---|---|
| Proporsi | ~5,5 kepala | **~3 kepala** — kepala besar, badan pendek gempal |
| Tangan & kaki | kurus | **tebal membulat**, tanpa pergelangan tipis |
| Detail kain | lipatan, kancing kecil | **dihapus**, blok warna polos |
| Mata | kecil | **besar sederhana**, ekspresif |
| Garis tepi | ada bayangan halus | **tanpa outline, tanpa gradasi** |

### Palette

| Warna | RGB | Untuk |
|---|---|---|
| Kuning marigold | `247, 181, 41` | Selendang, bunga |
| Hijau kamen | `124, 179, 66` | Kain bawah |
| Kulit | `240, 205, 170` | Wajah, tangan, kaki |
| Hitam | `30, 30, 30` | Rambut, pupil |
| Putih | `255, 255, 255` | Udeng, baju |

> Catatan: karakter ini **orisinal**, bukan turunan langsung dari file Vecteezy. Referensi hanya dipakai sebagai acuan busana dan nuansa.

---

## 3. Cara kerjanya

### v1 — yang dibangun sekarang

```
[ketik teks + tag] → Azure TTS → audio + viseme + waktu kata
                                           ↓
                              Rive → avatar bicara & berekspresi
```

| Hal | Keputusan |
|---|---|
| Masukan | **Teks diketik manual** di kotak |
| TTS | Azure Speech, suara Inggris |
| Lipsync | 22 viseme Azure → 16 bentuk mulut |
| Ekspresi | Tag ditulis manual di teks |

### Status avatar — v1

| Status | Kapan | Tampilan |
|---|---|---|
| **Diam** | tidak ada aktivitas | Napas, kedip, mata ikut cursor |
| **Ngomong** | audio berjalan | Lipsync + ekspresi dari tag |

### Ekspresi lewat tag

Tag ditulis langsung di kotak teks:

```
[senyum] Hey there! [kaget] Whoa, that's a great question. [ketawa] Just kidding.
```

Tag tidak diucapkan. Tag asing dibuang. Pencocokan lewat posisi kata (`wordBoundary`), karena suara Dragon HD tidak mengirim bookmark.

Format tag ini sengaja dibuat sama dengan yang nanti dipakai v2 — jadi waktu DeepSeek masuk, ia tinggal menghasilkan teks bertag yang sama persis, tanpa mengubah apa pun di sisi avatar.

### v2 — ditunda

```
[tahan tombol] → mic → Azure STT → DeepSeek → teks + tag → (alur v1)
```

| Hal | Rencana |
|---|---|
| Mulai bicara | Push-to-talk — tahan tombol |
| Nyela | Menekan tombol bicara menghentikan Wayan |
| STT | Azure Speech |
| LLM | DeepSeek (API kompatibel OpenAI, streaming) |
| Status tambahan | **Dengerin** (mata fokus ke depan), **Mikir** (mata lirik ke atas) |

---

## 4. Lingkup v1

### Wajib

- [ ] Lipsync 22 viseme Azure → 16 bentuk mulut
- [ ] Ekspresi lewat tag: netral, senyum, kaget, sedih, ketawa
- [ ] Idle hidup: napas, kedip, mata ikut cursor
- [ ] Gerak badan full body ala Duolingo (squash & stretch)
- [ ] Kotak teks manual + tombol Speak
- [ ] Halaman QC: 22 viseme, mulut kita vs gambar acuan Azure
- [ ] Online, repo GitHub **private**

### Ditunda ke v2

- Percakapan suara: mikrofon, push-to-talk, nyela
- Azure STT
- DeepSeek
- Status **Dengerin** dan **Mikir**

### Ditunda, belum dijadwalkan

- Background dan properti tambahan
- Bahasa Indonesia
- Karakter kedua
- Gestur tangan spesifik (melambai, menunjuk)

---

## 5. Biaya & batasan

### Recraft — saldo tersisa $4.90

Kalau **semua aset** digenerate di Recraft (cara yang ditulis di catatan Obsidian):

| Kelompok | Jumlah | Biaya |
|---|---|---|
| Konsep | 3 | $0.24 |
| Master final | 2 | $0.16 |
| Style | 1 | $0.005 |
| Base wajah | 1 | $0.08 |
| Mata & alis | 3 | $0.24 |
| **Mulut lipsync** | **14** | **$1.12** |
| Mulut ekspresi | 2 | $0.16 |
| Bagian badan | 8 | $0.64 |
| **Subtotal tanpa revisi** | | **$2.64** |
| Realistis (±2× revisi) | | **$4.50 – $5.30** |

**Ini melebihi saldo.** Dan angka itu belum termasuk kegagalan penyelarasan antar-aset.

### Rekomendasi: jangan generate semuanya di Recraft

Generate **satu master full body** saja di Recraft, lalu **pisahkan bagian dan gambar 16 bentuk mulut langsung di Rive**.

| | Semua di Recraft | Master + kerja Rive |
|---|---|---|
| Biaya | $4.50 – $5.30 | **$0.50 – $0.80** |
| Penyelarasan mulut | tiap hasil render ulang, posisi bisa geser | **sempurna**, satu kanvas |
| Kualitas path | bervariasi | terkendali |
| Waktu | ~2 jam nunggu API | lebih cepat |

Alasannya: bentuk mulut itu **bidang kecil dan sederhana** — menggambarnya di Rive jauh lebih cepat dan presisi daripada membujuk AI menghasilkan 14 gambar yang sejajar sempurna. Project lama membuktikan 22 viseme yang digambar manual di Rive berhasil.

Selain itu, `inpaint` Recraft **hanya ada di model V3**, sementara master kita pakai V4.1. Karena `style_id` terikat ke model, bagian hasil inpaint akan melenceng gayanya.

### Batasan lain

| Hal | Catatan |
|---|---|
| Kecepatan Recraft | Terukur **>120 detik** per panggilan, bukan ~13 detik seperti klaim dokumen. Semua panggilan harus background |
| Bones di Rive | **MCP tidak bisa membuat bone.** Rozi yang bikin manual di editor, baru AI yang mengikat dan menganimasikan |
| Akun Rive Free | Ada splash hitam "RIVE" ±3 detik, dan backup `.rev` butuh plan berbayar |
| Biaya Azure | v1 cuma TTS, ±$16–22 per 1 juta karakter. Karena online, **wajib ada pembatas panjang teks**. STT baru ikut menambah di v2 |
| Key di repo | Repo private, tapi key tetap **tidak boleh ter-commit**. Semua lewat `.env` + backend |

---

## 6. Risiko

| Risiko | Dampak | Penanganan |
|---|---|---|
| Recraft gagal bikin proporsi chunky yang konsisten | Konsep harus diulang, kredit habis | Kunci lewat prompt eksplisit + `random_seed`; uji 3 kandidat dulu |
| SVG Recraft terlalu banyak path untuk di-rig | Tidak bisa dianimasikan | Periksa jumlah path sebelum lanjut; target di bawah ~30 path |
| Squash & stretch ala Duolingo terlalu berat | Animasi tidak sempurna | Mulai dari napas + bounce sederhana, tambah bertahap |
| Biaya Azure membengkak saat dipamerkan | Tagihan tak terduga | Batasi panjang teks per permintaan |
| *(v2)* Nyela bikin audio tumpang tindih | Suara kacau | Hentikan audio dan reset state machine sebelum rekaman mulai |
| *(v2)* DeepSeek tidak patuh menyisipkan tag | Ekspresi tidak jalan | Tegaskan di system prompt + validasi; kalau tidak ada tag, pakai netral |

---

## 7. Keputusan yang sudah dikunci

| # | Keputusan | Alasan |
|---|---|---|
| 1 | REST API Recraft, bukan MCP | MCP pakai dompet subscription, kredit Rozi di API units |
| 2 | Model vector asli, bukan auto-trace | Terukur: trace 210 path vs vector asli 8 path — tidak bisa di-rig |
| 3 | Referensi Vecteezy **tidak** dipakai sebagai `style_reference` | Akan menarik hasil ke gaya Vecteezy, padahal kita mau gaya Duolingo |
| 4 | Pose berdiri, tangan di samping | Kalau tangan menyatu di depan, lengan tidak bisa dipisah untuk rigging |
| 5 | Inggris saja | Kualitas suara dan ketawa Azure paling bagus; fokus testing |
| 6 | Semua aset dibuat baru | Vault Obsidian & project `avatar-ai` hanya referensi pengetahuan |
| 7 | v1 pakai teks manual, LLM ditunda | Lipsync harus terbukti pas dulu; menumpuk STT + LLM di atas lipsync yang belum beres bikin sulit melacak sumber masalah |
| 8 | Master dari **app Gemini + vectorize Recraft**, bukan vector langsung Recraft | Generate vector Recraft kalah jauh secara kualitas; model raster lebih kuat, dan `/vectorize` Recraft menghasilkan 42 path bersih dari sumber datar |
| 9 | Latar sumber harus **biru polos**, lalu dihapus dari SVG | Latar putih membuat baju putih hilang saat vectorize; latar hijau akan menghilangkan kamen |

---

Roadmap pengerjaan: [ROADMAP.md](ROADMAP.md)

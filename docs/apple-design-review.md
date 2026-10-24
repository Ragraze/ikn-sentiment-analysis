# Design review: IKN Sentiment Lab

## Summary

Penilaian berbasis kode: **Good**. Aplikasi web Next.js untuk meneliti opini IKN ini membutuhkan alur yang mudah diulang: isi kalimat, baca sentimen dan topik, lalu gunakan hasilnya dalam penelitian. Penyempurnaan berfokus pada alur tersebut, pencarian dataset, dan keterbacaan metrik.

Pengguna meminta skill apple-design, dengan sidebar dan grafik tetap seperti sebelumnya. Prinsip HIG diterjemahkan ke elemen HTML, CSS semantic tokens, ARIA, serta keyboard browser; konvensi menu bar atau kontrol jendela macOS tidak diterapkan pada web ini. Antislop tidak digunakan pada tahap ini.

Koreksi setelah implementasi: underline pada menu aktif dihapus atas permintaan pengguna. Analisis, dataset, topik, dan evaluasi memakai satu judul halaman; judul panel berulang dihapus dan kontrolnya tetap tersedia. Evaluasi ditetapkan ke hasil notebook tanpa pemilih checkpoint. Heading editor/hasil serta aria-current tetap menjaga struktur dan konteks navigasi.

## Improvements yang diterapkan

| Prioritas | Temuan dan perbaikan | Dasar HIG |
| --- | --- | --- |
| High | Isian dan hasil hilang ketika meninggalkan halaman analisis. Context pada layout root kini menyimpan sesi selama navigasi; reload mengosongkannya. Data ini tidak ditulis ke penyimpanan browser. | `entering-data.md › Entering data`: “minimize the amount of data that people need to supply” |
| High | Pengosongan form langsung membuang isian. Tombol Urungkan kini memulihkan kalimat dan hasil yang sesuai. Mengedit kalimat membatalkan hasil lama dan response yang terlambat tidak boleh menggantikannya. | `feedback.md › Best practices`: “help them understand why”; pola pemulihan tanpa dialog merupakan penilaian desain untuk tindakan yang bisa dibalik. |
| High | Ekspor bisa memakai pencarian sebelumnya selama debounce. Ekspor serta pagination kini ditahan sampai filter diterapkan dan request selesai; ringkasan filter menjelaskan cakupan data. | `feedback.md › Best practices`: “Show people when a command can’t be carried out” |
| Medium | Pengisian, tindakan, dan hasil belum memiliki hirarki tugas yang cukup jelas. Editor, contoh isian, tombol analisis, dan toolbar hasil kini dipisahkan menurut fungsinya. | `layout.md › Visual hierarchy`: “Group related items to clearly express related information or functions.” |
| Medium | Kesalahan isian dan kegagalan layanan perlu ditangani berbeda. Validasi muncul dekat textarea dengan aria-describedby; kegagalan layanan tidak memberi aria-invalid pada kalimat yang valid. | `entering-data.md › Best practices`: “Dynamically validate field values.” |
| Medium | Belum ada jalur cepat untuk pekerjaan berulang. Ctrl/Cmd + Enter memicu analisis dari textarea; Escape membatalkan tampilan request aktif; salin hasil menampilkan feedback di dekat tombol. | `keyboards.md › Custom keyboard shortcuts`: “only the most frequently used app-specific commands” |
| Medium | Loading perlu terasa jelas tanpa perkiraan kemajuan buatan. Indikator progress native tanpa value menandai proses tak tentu, dengan teks konteks dan kontrol Batalkan. Pembatalan request browser tidak menjamin komputasi backend berhenti. | `loading.md › Showing progress`: “use an indeterminate progress indicator when you don’t” |
| Medium | Tabel panjang sulit dipindai, dan jumlah delapan baris kurang fleksibel. Baris bergantian, pengaturan 8/16/32/50 opini, reset filter, serta tindakan keluar dari hasil kosong ditambahkan. | `lists-and-tables.md › Desktop (macOS)`: “Consider using alternating row colors in a multicolumn table.” |
| Low | Istilah evaluasi memerlukan penjelasan yang bisa dibuka saat dibutuhkan. Konteks sumber dan definisi akurasi, precision, recall, serta F1 tersedia di luar visualisasi. | `layout.md › Visual hierarchy`: “Use progressive disclosure to make layouts cleaner and easier to interact with.” |

## Token dan susunan

Token yang sudah ada dipakai kembali. Tidak ada perubahan pada palet sidebar maupun grafik. Kontras dihitung langsung dengan rumus WCAG dari nilai CSS, mengikuti `accessibility.md › Vision` dan `color.md › Inclusive color`.

| Peran | Terang | Gelap | Kontras yang diperiksa |
| --- | --- | --- | --- |
| Permukaan | #ffffff | #202622 | Teks utama: 15,25:1 / 13,52:1 |
| Kelompok sekunder | #eef1ef | #2b332e | Teks sekunder: 5,66:1 / 6,77:1 |
| Teks utama | #202724 | #edf1ee | Terhadap permukaan: 15,25:1 / 13,52:1 |
| Teks sekunder | #56615c | #b2beb6 | Terhadap permukaan: 6,44:1 / 8,03:1 |
| Aksi | #1f6256 | #97cdbb | Terhadap permukaan: 7,14:1 / 8,64:1 |
| Kesalahan | #91483f | #e2a99f | Terhadap permukaan: 6,56:1 / 7,64:1 |

Typeface tetap sistem. Judul editor 16 px, toolbar hasil 18 px, isian 16 px, isi 14–16 px, dan teks pendamping 13 px memakai rem. Kontrol mempertahankan target minimum 44 px. Kelompok kontrol bisa membungkus dan teks tidak diberi tinggi tetap, sesuai `typography.md › Supporting Dynamic Type`.

```text
Lebar biasa                       Lebar sempit
Editor opini | Toolbar hasil      Editor opini
Textarea     | Salin hasil        Textarea dan contoh
Contoh       | Skor (tetap)       Analisis, Kosongkan/Urungkan
Analisis     | Topik (tetap)      Toolbar hasil dan Salin
Urungkan     | Detail             Skor, topik, detail
```

Ciri yang dipertahankan adalah pembacaan satu opini melalui dua model dengan satuan skor berbeda: persentase sentimen dan cosine topik. Perubahan ini berasal dari kebutuhan riset IKN. Alur tiga label dekoratif pada form digantikan petunjuk kontekstual; tidak ada penambahan efek material atau motion untuk meniru aplikasi native.

## What works

Pada tahap awal, tujuh file sidebar/dashboard/grafik utama/CSS global/status diverifikasi identik dengan baseline; koreksi lanjutan pengguna kemudian menghapus underline dari CSS sidebar. Grafik dashboard, struktur batang skor sentimen, grafik topik, dan confusion matrix dipertahankan. Tautan internal memakai Next.js Link agar perpindahan halaman tidak memuat ulang sesi. Stylesheet tambahan dibatasi pada workspace fitur, termasuk toolbar sumber topik setelah judul berulang dihapus.

Form memakai textarea, button, progress, serta details native. Clear dapat dipulihkan, status diumumkan tanpa dialog, label input tetap terlihat, dan batas antara hasil model serta penjelasan pengguna tetap jelas. Skor tidak diberi nama kategori baru yang tidak berasal dari model.

## Validation dan batas cakupan

- Typecheck serta build produksi Next.js berhasil.
- 20 tes frontend memeriksa API, rendering topik/grafik, validasi kalimat, pemulihan sesi, penolakan hasil usang, serta format laporan yang disalin.
- Tes render produksi memeriksa kelima route, kontrol baru, pilihan sumber, nonce CSP, dan pemisahan konten.
- Tidak ada perubahan pada backend, checkpoint, atau dataset.
- Pemeriksaan browser, klik, clipboard, navigasi keyboard/IME, dan tampilan pada zoom nyata belum dapat dijalankan di lingkungan ini. Socket lokal ditolak dan browser tidak tersedia; hasil kode tidak dinyatakan sebagai hasil interaksi langsung.

## References yang dibaca

`accessibility.md`, `layout.md`, `typography.md`, `color.md`, `designing-for-macos.md`, `entering-data.md`, `text-fields.md`, `lists-and-tables.md`, `feedback.md`, `loading.md`, `keyboards.md`, serta `cross-platform.md` dari skill apple-design. Panduan `code-audit.md` dibaca untuk memetakan cakupan; aplikasi ini tidak memiliki Apple Pay, Liquid Glass, atau integrasi perangkat Apple khusus.

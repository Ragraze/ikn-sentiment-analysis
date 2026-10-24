# Pemeriksaan antislop: dashboard sidebar

Arahan pengguna: navigasi sidebar dan halaman utama dengan grafik. ENERGY 2 / RHYTHM 2 / MOTION 1. Alasan visual dan komposisi tercatat pada [design-notes.md](design-notes.md).

## Hard gate

- R-02 PASS: teks pada komponen baru tidak memakai em dash.
- R-03 PEMERIKSAAN KODE: grid minmax, sidebar desktop pada 64 rem, dialog mobile, ringkasan dua/empat kolom, grafik fleksibel, dan area gulir tabel tersedia. Belum diverifikasi di viewport browser.
- R-17/R-18/R-36/R-38 PASS: jumlah, persentase, dan grafik berasal dari API summary/topics. Tidak ada statistik, avatar, testimonial, atau deret waktu rekaan.
- R-23 PASS: struktur sidebar dan grafik sesuai permintaan pengguna. Identitas aplikasi tetap berupa teks; ikon menu menggambarkan tujuan navigasinya.
- R-24 PASS: tes produksi membuka /, /analysis, /dataset, /topics, dan /evaluation; tiap halaman memiliki tautan sidebar yang aktif dan konten sesuai route.
- R-25 PASS: 42 pasangan warna per tema diperiksa; minimum kontras teks 4,70:1 terang dan 4,747:1 gelap. Kontrol dan warna data yang diperiksa memenuhi 3:1.
- R-26 PEMERIKSAAN KODE: setiap kontrol memiliki route, handler, atau perilaku HTML native. Daftar kontrol tercatat di bawah.
- R-27 PASS PADA KODE: grafik dan layanan data memiliki loading, error, serta empty state; data kosong tidak digambar sebagai data bernilai rekaan.
- R-28 PASS: tidak ada FAQ.
- R-32 PEMERIKSAAN KODE: fokus terlihat, skip link tersedia, dialog native menangani fokus dan Escape, grafik memiliki deskripsi dan angka alternatif. Belum diuji dengan keyboard nyata.
- R-33 PASS: source komponen dan CSS ditulis langsung, tanpa script penggantian teks untuk membangun UI.
- R-34 PEMERIKSAAN KODE: tema sistem memakai token yang diperiksa kontrasnya. Belum diperiksa secara visual di browser.
- R-35 BUILD/RENDER PASS, BROWSER BELUM DIVERIFIKASI: build Next.js dan rendering semua route berhasil; browser tidak tersedia dan socket lokal ditolak EPERM.
- R-37 PASS: arah sidebar, halaman utama, dan grafik berasal dari permintaan pengguna.

## Purpose gate dan kualitas

- R-01/R-07/R-10/R-12/R-13 PASS: palet hijau lama dipertahankan, tanpa gradient, glow, kaca, tekstur dekoratif, atau bayangan berulang.
- R-04 PASS: glyph menu sesuai fungsi halaman dan dilengkapi teks; tidak memakai ikon pemasaran AI.
- R-06/R-31 PASS: font sistem untuk keterbacaan; tabular numerals untuk angka penelitian; alasan warna, struktur, dan grafik terdokumentasi.
- R-08/R-09/R-15/R-16 PASS: tindakan berlabel spesifik tanpa panah dekoratif, badge pemasaran, atau klaim AI.
- R-14/R-20/R-22/R-30 PASS SEBAGAI PENILAIAN KODE: grafik menjawab pertanyaan dataset IKN; sidebar adalah struktur yang diminta pengguna; tidak ada ilustrasi atau replika produk lain.
- R-19 PASS PADA KODE: transisi hover dibatasi dan reduced motion menonaktifkannya.
- Dials dan fokus PASS PADA KODE: sidebar memisahkan navigasi; grafik sentimen menjadi fokus halaman utama; analisis kalimat memiliki halaman khusus.
- C-1/C-3/C-5 PASS PADA KODE: struktur mengikuti tugas penelitian, semua statistik mempunyai sumber, dan alasan teknik tercatat.
- C-2/C-4 PEMERIKSAAN KODE: kontrol, state, dan breakpoint tersedia; interaksi browser belum diverifikasi.
- R-05/R-11/R-21/R-29 PASS PADA KODE: komposisi ringkasan, grafik, dan status berbeda sesuai kebutuhan; radius konsisten; tema sistem dan palet semantik dipertahankan.

## Kontrol dan bukti

| Kontrol | Perilaku / bukti |
| --- | --- |
| Lima menu sidebar | Route terpisah; tes render memastikan tujuan, aria-current, dan konten halaman |
| Menu seluler | showModal membuka dialog; keadaan tertutup tersedia pada hasil render |
| Tutup, Escape, backdrop | Menutup dialog; kode membersihkan kunci gulir latar |
| Perpindahan route / ukuran desktop | Menutup dialog bila masih terbuka |
| Langsung ke konten | Anchor menuju main dengan tabindex -1 |
| Filter proporsi sentimen | Mengganti counts dari summary untuk semua data atau split terpilih |
| Lihat angka pada grafik | Details native membuka tabel sembilan nilai sentimen per split; angka diuji rendering |
| Sumber topik | Mengganti request notebook/trained; tautan detail membawa sumber yang sama |
| Detail sumber notebook | Tes render /topics?source=notebook memeriksa pilihan sumber |
| Periksa ulang layanan | Memuat ulang health melalui context bersama |
| Analisis kalimat / Telusuri dataset | Route /analysis dan /dataset yang telah diuji rendering |
| Kontrol dataset, evaluasi, prediksi, kata kunci | Fitur lama berada pada halaman masing-masing; tautan lintas fitur diperbarui |

Enam tes komponen memeriksa hasil topik dan grafik, termasuk data nol, satu kategori, label angka, serta tabel alternatif. Sepuluh tes API frontend tetap lulus. Ini merupakan verifikasi kode dan rendering server, bukan klaim click-through browser.

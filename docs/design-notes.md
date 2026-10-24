# Arah tampilan

Penyempurnaan terbaru memakai **apple-design** sesuai permintaan pengguna, dengan tampilan sidebar dan grafik dipertahankan. Pekerjaan difokuskan pada hierarki form, draft selama navigasi, undo, keyboard, salin hasil, filter dataset, serta penjelasan evaluasi. Antislop tidak digunakan untuk tahap ini. Alasan dan rujukan HIG tersedia pada [apple-design-review.md](apple-design-review.md).

Koreksi pengguna berikutnya: hapus underline menu aktif, gunakan satu judul utama pada analisis/dataset/topik/evaluasi, dan tampilkan evaluasi notebook saja. Judul panel yang mengulang judul halaman dihapus; heading untuk bagian kerja seperti editor dan hasil tetap tersedia.

Arahan terbaru pengguna: dashboard dengan navigasi sidebar dan halaman utama disertai grafik. Palet hijau yang sudah ada dipertahankan, dengan konten riset sebagai pusat perhatian.

Pembacaan desain: dashboard penelitian opini IKN untuk peneliti dan pembaca data, dengan sidebar hijau hutan, ruang kerja netral, dan grafik berlabel. ENERGY 2 / RHYTHM 2 / MOTION 1.

## Struktur dan alasan

- Sidebar menjadi satu-satunya navigasi utama pada desktop agar perpindahan antara ringkasan, analisis kalimat, dataset, topik, dan evaluasi mudah ditemukan. Setiap tujuan memiliki route sendiri.
- Halaman utama menjawab tiga pertanyaan: bagaimana komposisi sentimen, bagaimana jumlahnya pada tiap bagian dataset, dan berapa topik yang ditemukan per sentimen.
- Ringkasan total, training, validasi, dan pengujian ditempatkan dalam satu bidang agar hubungan bagian dengan keseluruhan terlihat. Total diberi latar hijau muda untuk menandai agregat.
- Grafik donat menjelaskan proporsi sentimen dengan jumlah dan persentase tertulis di sampingnya. Filter bagian data memperbarui angka dan grafik dari respons summary yang sama.
- Grafik batang berkelompok membandingkan jumlah sentimen pada training, validasi, dan pengujian dengan skala yang sama. Tabel dalam details menyediakan angka tepat dan akses tanpa mengandalkan warna.
- Grafik batang horizontal untuk jumlah topik memakai laporan Top2Vec proyek atau notebook sesuai pilihan pengguna. Tautan detail meneruskan sumber pilihan tersebut melalui query parameter.
- Grafik sentimen memakai label asli penelitian, sedangkan topik memakai kelompok prediksi IndoBERT. Keterangan sumber menjelaskan perbedaan ini; tidak ada deret waktu atau data buatan.
- Status IndoBERT dan Top2Vec tersedia pada dashboard dan halaman analisis. Tombol periksa ulang meminta status terbaru dari backend.

## Bahasa visual

- Hijau hutan membedakan sidebar dari area analisis. Item aktif memiliki permukaan terang, bobot teks lebih tebal, dan aria-current. Underline dihapus sesuai koreksi pengguna; indikator fokus keyboard tetap tersedia.
- Ikon SVG pada menu menunjukkan ringkasan, percakapan, tabel, hubungan topik, dan evaluasi. Ikon membantu pemindaian menu, selalu disertai teks, dan tidak menjadi logo aplikasi.
- Font sistem menjaga keterbacaan tanpa unduhan font. Angka menggunakan tabular numerals agar jumlah dan skor mudah dibandingkan.
- Permukaan putih pada abu kehijauan mengelompokkan grafik. Radius 6 px untuk kontrol, 7 px untuk menu, 8 px untuk kartu topik, dan 12 px untuk panel.
- Warna sentimen bersifat semantik dan selalu memiliki label. Diagram donat memakai pemisah permukaan; batang berkelompok memiliki jarak antar-kategori.
- Tidak ada animasi grafik yang berjalan terus-menerus. Transisi hanya pada hover; reduced motion dan forced colors memiliki aturan tersendiri.
- Tema terang/gelap mengikuti preferensi sistem.

## Layar kecil dan aksesibilitas

Sidebar tetap pada desktop mulai 64 rem. Pada layar lebih kecil, tombol Menu membuka dialog native di sisi kiri. Dialog menangani pembatasan fokus dan Escape, sementara tombol tutup, klik backdrop, pemilihan tujuan, serta perubahan ke ukuran desktop menutup panel. Gulir halaman latar dikunci selama dialog terbuka.

Ringkasan empat kolom menjadi dua kolom pada layar sempit. Grafik tersusun satu kolom hingga ruang kerja cukup lebar; donat dan legendanya dapat bertumpuk. Tabel data grafik memiliki area gulir bernama. Target kontrol minimal 44 px, fokus terlihat, dan tautan langsung ke konten tersedia.

Kontras token diperiksa pada kedua tema. Pemeriksaan visual dan keyboard langsung memerlukan browser; lingkungan pengembangan saat ini tidak menyediakan browser dan menolak socket lokal. Bukti yang tersedia dicatat pada verification.md dan antislop-check.md.

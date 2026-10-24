# Verifikasi struktur, tampilan, dan keamanan

Tanggal: 24 Oktober 2026.

## Koreksi sidebar, judul, dan evaluasi

Underline pada menu sidebar aktif dihapus sesuai permintaan pengguna. Setiap halaman tetap memiliki satu h1; judul panel yang mengulang analisis, dataset, pemodelan topik, atau evaluasi dihapus. Header bagian kerja seperti editor dan hasil menggunakan h2. Halaman evaluasi meminta `/api/evaluation?source=notebook` secara tetap dan tidak menyediakan pilihan checkpoint.

Endpoint notebook diverifikasi HTTP 200: `test_with_predictions new.csv`, 2.501 opini, akurasi 0,7760895642, Macro F1 0,6393119094. Typecheck dan pengujian frontend lulus; tes render memeriksa satu h1 per halaman, tidak adanya judul panel berulang, dan sumber notebook tanpa pemilih sumber evaluasi.

## Penyempurnaan dengan apple-design

Perubahan mengikuti permintaan pengguna untuk memakai apple-design sambil mempertahankan tampilan sidebar dan grafik. Form mendapat validasi dekat isian, pintasan Ctrl/Cmd + Enter, draft dalam memori selama navigasi, undo pengosongan, salin hasil dengan feedback, serta indikator loading native. Dataset mendapat ringkasan/reset filter, pilihan jumlah baris, dan ekspor yang menunggu filter selesai. Evaluasi mendapat penjelasan sumber dan metrik di luar visualisasi.

Typecheck dan build produksi berhasil. Sebanyak 20 tes frontend lulus, termasuk pemulihan kalimat beserta hasilnya, penolakan respons usang, validasi, serta format laporan yang disalin. Tes render produksi memeriksa kelima route, kontrol baru, sumber topik, dan nonce CSP. Tujuh file sidebar/dashboard/grafik utama/CSS global/status/loading identik dengan baseline; source grafik topik juga dipertahankan, dengan perubahan hanya pada tautan internal. CSS tambahan dibatasi pada tiga workspace fitur.

Kontras teks fitur baru dihitung langsung dari token CSS: minimum 5,664:1 terang dan 6,443:1 gelap pada pasangan yang digunakan. Rincian HIG dan token tersedia pada [apple-design-review.md](apple-design-review.md). Browser tidak tersedia, sehingga clipboard, klik, fokus keyboard, dan ukuran layar nyata belum diverifikasi langsung.

## Pembaruan dashboard sidebar

Navigasi desktop kini berupa sidebar dengan halaman terpisah untuk dashboard, analisis kalimat, dataset, topik, dan evaluasi. Halaman utama memuat ringkasan dataset, grafik donat proporsi sentimen dengan filter split, grafik batang perbandingan split, grafik jumlah topik dengan pilihan sumber, dan status layanan model.

| Pemeriksaan | Hasil |
| --- | --- |
| `npm run typecheck` dan build TypeScript | Lulus |
| Tes frontend | 16 tes lulus: 10 API dan 6 komponen topik/grafik |
| `npm run build` | Kelima route berhasil dibangun |
| `npm run test:render` | Kelima route HTTP 200; active sidebar, konten per halaman, dialog seluler, sumber notebook pada detail, nonce CSP, dan header valid |
| Kontras | 42 pasangan per tema, minimum teks 4,70:1 terang dan 4,747:1 gelap; pasangan kontrol dan grafik yang diperiksa memenuhi 3:1 |

Tes grafik mencakup jumlah dan persentase pada deskripsi aksesibel, input tanpa opini, satu kategori, serta tabel perbandingan sembilan angka sentimen/split. Grafik tidak mengarang data waktu atau tren. Sidebar memakai dialog native pada layar kecil, dan seluruh tujuan navigasi merupakan route yang benar-benar dibangun.

Pemeriksaan ini dilakukan melalui build, tes komponen, dan request/response Next.js dalam memori. Browser tidak tersedia dan percobaan socket lokal ditolak `EPERM`; pemeriksaan visual, klik, fokus modal, dan ukuran viewport nyata belum diverifikasi langsung. Detail keputusan dan pemeriksaan tersedia di [design-notes.md](design-notes.md) dan [antislop-check.md](antislop-check.md).

## Pembaruan analisis topik dan navigasi

Analisis kalimat sekarang menyertakan `topic_analysis` dari model Top2Vec sesuai hasil sentimen IndoBERT. Hasil menampilkan kata kunci, cosine, jumlah dokumen dalam topik, dan topik pembanding. Laporan topik menampilkan bobot kata ketika tersedia. Navbar memakai hijau hutan, posisi sticky, penanda bagian aktif, akses langsung ke form, dan menu layar kecil.

| Pemeriksaan terbaru | Hasil |
| --- | --- |
| `make test` | 59 tes backend lulus; typecheck dan tes frontend berhasil |
| Tes frontend dijalankan per file | 10 tes API dan 3 tes rendering hasil topik lulus |
| `npm run build` | Build produksi berhasil |
| `npm run test:render` | Rendering produksi, nonce CSP, kelima tujuan navigasi, penanda aktif awal, kontrol menu, dan judul fitur berhasil |
| Inferensi gabungan dengan model asli | Tiga contoh positif, negatif, dan netral menghasilkan HTTP 200, `topic_analysis.available=true`, `matched=true`, serta topik dan kata kunci dari model terlatih |
| Laporan Top2Vec proyek | 2 topik positif (305 dokumen), 2 netral (328), dan 3 negatif (1.868); coherence masing-masing 0,4048, 0,3295, dan 0,6173 |
| CLI `train_topics.py --help` | Argumen model, laporan, worker, dan sumber data berhasil dimuat |
| Kontras warna | 38 pasangan per tema diperiksa dengan fungsi `antislop-human/contrast-check.py`; minimum teks 4,70:1 pada terang dan 4,747:1 pada gelap; batas kontrol/grafik/fokus yang diperiksa mencapai 3:1 |

Tes topik menggunakan test double untuk kontrak `Top2Vec.load`, `query_topics`, dan `get_topic_sizes`. Tes mencakup pemilihan model per sentimen, penggunaan teks hasil preprocessing, caching, kata tidak dikenal, skor negatif/nonfinite, kegagalan model, pemulihan status, serta direktori yang dikonfigurasi. Direktori topik pada pengujian API diisolasi agar pengujian model hilang tetap valid setelah artefak sungguhan terpasang.

Instalasi awal sempat terhambat DNS. Setelah pengguna menyelesaikan instalasi dan training, tiga model Top2Vec beserta `reports/topics.json` ditemukan dan diuji menggunakan test client Flask dengan checkpoint IndoBERT asli. Laporan bertanggal `2026-10-24T15:17:58.784496+00:00`, memakai `doc2vec`, `deep-learn`, `min_count=10`, dan 4 worker pada `test_with_predictions_and_coherence.csv`.

Contoh “Saya mendukung pembangunan ibu kota Nusantara.” menghasilkan sentimen positif dengan confidence 0,8921 dan cosine topik terdekat 0,6854. Contoh kritik anggaran menghasilkan sentimen negatif dengan confidence 0,9355 dan cosine 0,1169; contoh lokasi IKN menghasilkan sentimen netral dengan confidence 0,5763 dan cosine 0,0776. Pengujian ini membuktikan alur inferensi berjalan; kemiripan yang rendah pada dua contoh terakhir menunjukkan relevansi topik perlu dinilai dari konteks. Nilai cosine Doc2Vec dapat berubah antar-inferensi.

Browser tidak tersedia dan sandbox menolak pembuatan socket (`EPERM`). Pemeriksaan visual pada viewport, click-through, serta pengujian keyboard langsung belum dilakukan. Respons produksi diuji dalam memori, bukan melalui server HTTP yang dibuka pada port.

## Struktur dan kompatibilitas

- Data dipisahkan ke `data/raw`, `data/processed`, `data/external`, dan `data/predictions`.
- Tiga notebook dipindahkan ke `notebooks/`.
- Source frontend ditempatkan di `dashboard/frontend/src/`; alias TypeScript dan pengujian API diperbarui.
- Virtual environment, checkpoint, dan direktori laporan tetap pada lokasi aplikasi yang sudah digunakan.
- SHA-256 seluruh 13 file data, kamus, dan notebook sesuai sebelum pemindahan. Pemetaan jalur dan checksum dicatat pada [data-integrity.json](data-integrity.json).

## Pemeriksaan

| Pemeriksaan | Hasil |
| --- | --- |
| `make test-backend` | 45 pengujian lulus, termasuk data, API, checkpoint, paralelisme, rate limit, Origin/Host, CSV, dan arsip berbahaya |
| `npm run typecheck` | Lulus |
| `npm test` | 10 pengujian frontend lulus |
| `npm run build` | Build produksi berhasil |
| `npm run test:render` | Rendering produksi berhasil; seluruh 13 script memakai nonce respons yang benar; dua respons memiliki nonce berbeda; header dan tujuan navigasi benar |
| CLI training, evaluasi, Top2Vec, dan impor checkpoint dengan `--help` | Entrypoint berhasil dimuat |
| `bash -n scripts/setup_backend.sh` | Sintaks shell valid |
| `pip check` | Tidak ada konflik dependensi |
| Prediksi checkpoint lokal melalui test client Flask | HTTP 200; label `positive`; confidence 0,892081 |

Kalimat uji inferensi: “Saya mendukung pembangunan ibu kota Nusantara.” Teks hasil preprocessing: `dukung bangun kota nusantara`.

## Tampilan

Arahan pengguna: aksen minimal. Identitas aplikasi memakai nama teks, warna netral, dan aksen hijau terbatas. Font sistem dan ukuran berbasis rem meningkatkan keterbacaan; slogan, simbol hias, nomor bagian dekoratif, chip kata berulang, dan kartu angka terpisah dihapus. Grafik batang menyertakan label, jumlah, dan persentase.

Frontend dipisahkan per fitur; request data bersama memiliki loading, error, empty state, pembatalan, serta batas waktu. Analisis kalimat hanya dipicu tombol. Mengubah teks membatalkan request tampilan yang berjalan dan menghapus hasil lama. Model tidak lagi dijalankan otomatis pada setiap jeda mengetik.

Kontras dihitung dengan `antislop-human/contrast-check.py` untuk pasangan token teks pada empat permukaan dalam tema terang dan gelap. Seluruh pasangan teks yang diperiksa memenuhi 4,5:1; nilai terendah 4,70:1. Teks sekunder pada permukaan utama: 6,44:1 terang dan 8,03:1 gelap. Teks tombol utama: 7,14:1 terang. Batas kontrol dan indikator fokus diperiksa terhadap ambang 3:1.

CSS menyediakan susunan sempit, menengah, dan lebar; tabel opini berubah menjadi baris bertumpuk pada layar sempit. Tabel metrik menggunakan area gulir bernama yang dapat difokuskan dengan keyboard. Tema mengikuti sistem; reduced motion dan forced colors memiliki aturan khusus. Detail desain terdapat di [design-notes.md](design-notes.md).

## Status antislop

Mode: `during`, pilihan sesi. ENERGY 1 / RHYTHM 2 / MOTION 1. Pemeriksaan kode dan build dicatat pada [antislop-check.md](antislop-check.md). Verifikasi browser belum tersedia, sehingga tidak ada klaim bahwa gate interaksi visual sudah lulus penuh.

## Batas verifikasi

Sandbox menolak socket jaringan (`EPERM`) dan tidak menyediakan browser. Rendering produksi diuji memakai request/response dalam memori; click-through, screenshot pada ukuran layar berbeda, dan screen reader belum diuji langsung. Audit advisory npm gagal mengakses registry (`EAI_AGAIN`). [security.md](security.md) merinci perbaikan serta batas cakupan pemeriksaan keamanan.

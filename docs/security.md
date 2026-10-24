# Pemeriksaan keamanan

Tanggal: 24 Oktober 2026. Lingkup: frontend Next.js, API Flask, pembacaan dataset/laporan, preprocessing, tokenisasi, pemuatan model, dan skrip setup, training, evaluasi, ekspor, serta impor checkpoint. Notebook dipertahankan sebagai artefak penelitian; API membaca output topik tanpa mengeksekusi selnya.

## Perubahan

| Bagian | Perbaikan | Bukti |
| --- | --- | --- |
| Inferensi | Safetensors lokal diwajibkan; `trust_remote_code=False` dipertahankan; skor non-finite ditolak | Tes argumen loader dan inferensi checkpoint asli |
| Batas kerja | Satu prediksi aktif dan maksimal 30 percobaan per menit per proses; antrean tambahan ditolak | Tes paralel, HTTP 503, HTTP 429, dan `Retry-After` |
| Request | JSON dan batas ukuran tetap diperiksa; karakter kontrol, surrogate tidak valid, filter berulang, dan pencarian berlebih ditolak | Tes input dan query berbahaya |
| Origin & Host | Prediksi lintas situs ditolak; Host dibatasi melalui `IKN_TRUSTED_HOSTS` | Tes Origin asing, `null`, fetch cross-site, dan Host asing |
| Error | Detail exception model/laporan dicatat pada backend dan tidak dikirim ke pengguna | Tes error dengan diagnostic serta jalur internal |
| Ekspor CSV | Sel dikutip dan prefix formula, karakter kontrol awal, serta varian full-width ditangani | Tes CSV round-trip dan prefix formula |
| ZIP | Maksimal 128 entri, total 2 GiB, per file 1 GiB; file executable, symlink, path traversal, dan path duplikat ditolak | Tes arsip berbahaya dan pemasangan checkpoint sintetis |
| Script halaman | CSP memakai nonce acak per request dan `strict-dynamic`; produksi tidak mengizinkan arbitrary inline script atau eval | Tes rendering produksi untuk seluruh script pada dua respons |
| Header | `nosniff`, `DENY`, `no-referrer`, dan pembatasan izin kamera/mikrofon/lokasi | Tes konfigurasi dan rendering |
| Frontend | Request API dibatasi ke jalur relatif `/api/`; error transport disederhanakan; pembatalan dan deadline satu menit tersedia | Tes request eksternal, abort, respons salah, dan kode fetch |
| Data tidak lengkap | Kategori sentimen yang tidak muncul tetap memiliki jumlah nol | Tes dataset satu kategori |
| Integritas laporan | Laporan evaluasi dengan label, support, confusion matrix, atau skor yang tidak valid tidak dipublikasikan | Tes laporan korup dan nilai NaN |

Rendering halaman memerlukan request dinamis agar nonce dalam header dan script selalu sama. `style-src` tetap mengizinkan inline style untuk panjang batang grafik; izin tersebut tidak diterapkan pada script produksi. Pendekatan nonce mengikuti [dokumentasi CSP Next.js](https://nextjs.org/docs/app/guides/content-security-policy).

Pembatasan body, Host, dan header mengikuti [pertimbangan keamanan Flask](https://flask.palletsprojects.com/en/stable/web-security/). Pemilihan format model mengurangi permukaan deserialisasi, sesuai [kebijakan keamanan PyTorch](https://github.com/pytorch/pytorch/security/policy).

## Batas pemeriksaan

- Rate limit bersifat global per proses, bukan per pengguna atau antar-worker. Limiter aplikasi ini bukan pengganti pembatasan trafik di reverse proxy.
- Origin check bukan autentikasi. Layanan tetap untuk penggunaan lokal; `run.py` mengikat `127.0.0.1`. Jika dipublikasikan untuk data privat, autentikasi, HTTPS, konfigurasi Origin/Host, dan pembatasan trafik perlu ditetapkan pada lingkungan deployment.
- CSV yang diekspor untuk spreadsheet dapat mengandung prefix apostrof pada sel berisiko. Tidak ada sanitasi CSV yang universal untuk seluruh spreadsheet dan skenario penyimpanan ulang; lihat [OWASP CSV Injection](https://community.owasp.org/attacks/CSV_Injection).
- `pip check` memverifikasi konsistensi dependensi dan berhasil. Audit advisory npm tidak dapat diselesaikan karena akses registry gagal dengan `EAI_AGAIN`; hasil ini tidak menyatakan dependensi bebas CVE.
- Browser tidak tersedia dan sandbox menolak pembukaan port (`EPERM`). Rendering produksi dijalankan melalui request/response dalam memori; interaksi klik, tampilan pada ukuran layar nyata, dan pembacaan screen reader belum diverifikasi langsung.

Tidak ada perubahan pada isi data sumber, notebook, bobot model, urutan label, atau algoritme preprocessing penelitian.

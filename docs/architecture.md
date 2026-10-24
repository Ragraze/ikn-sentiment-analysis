# Struktur proyek

```text
sentiment-analysis/
├── data/
│   ├── raw/              CSV berlabel, sumber eksplorasi
│   ├── processed/        TSV input IndoBERT
│   ├── external/         Kamus slang dan stopword
│   └── predictions/      Prediksi historis notebook
├── notebooks/            Notebook dan output penelitian asli
├── dashboard/
│   ├── frontend/         Next.js: src/app, src/features, src/components, src/hooks, src/lib
│   ├── server/           API Flask dan layanan analisis
│   ├── scripts/          Setup, training, evaluasi, impor checkpoint
│   ├── tests/            Pengujian data, API, dan checkpoint
│   ├── config/           Parameter yang ditelusuri ke notebook
│   ├── models/           Checkpoint lokal
│   ├── reports/          Hasil evaluasi dan pemodelan topik lokal
│   └── run.py            Entrypoint API
└── docs/                 Arsitektur dan catatan verifikasi
```

Direktori aplikasi `dashboard/` dipertahankan agar perintah pengembangan, virtual environment, dan lokasi checkpoint yang sudah terpasang tetap berlaku. Data sumber dan artefak eksperimen dikelompokkan berdasarkan tanggung jawabnya.

## Aliran data

Browser meminta `/api/*` ke Next.js. Proxy Next.js meneruskan request ke Flask. `DatasetRepository` membaca CSV/TSV dan output notebook; `IndoBertService` memuat checkpoint lokal untuk prediksi. Top2Vec dilatih melalui CLI, lalu laporan JSON dibaca API.

Pada `POST /api/predict`, hasil sentimen dan teks hasil preprocessing diteruskan ke `Top2VecService`. Layanan memilih `model_top2vec_{sentiment}`, memuat model Doc2Vec lokal satu kali per proses, lalu memanggil `query_topics` untuk maksimal tiga topik. Kata yang seluruhnya tidak dikenal korpus menghasilkan `no_match`; model hilang atau gagal menghasilkan status yang tetap disertakan dalam respons sentimen HTTP 200. Tidak ada training atau unduhan embedding selama request. Pembatasan request dan semaphore inferensi mencakup seluruh analisis gabungan.

`GET /api/health` menyertakan status tiga model topik tanpa memuat bobot. `TOP2VEC_MODEL_DIR` dan `TOP2VEC_REPORT_DIR` digunakan backend maupun skrip training. Restart backend setelah mengganti artefak. Laporan notebook menyediakan eksplorasi hasil lama; pencocokan kalimat baru hanya menggunakan model Top2Vec terlatih, tanpa fallback pencarian kata pada laporan.

`server/settings.py` menentukan direktori data, notebook, dan konfigurasi penelitian. Resolver data mendukung susunan berkelompok serta direktori datar yang diberikan integrasi lama. Pemindahan file tidak mengubah urutan label, preprocessing, parameter model, isi dataset, atau hasil penelitian.

Frontend memisahkan tampilan per fitur di `src/features/`. Komponen bersama berada di `src/components/`, siklus request yang bisa dibatalkan di `src/hooks/`, dan kontrak data serta format angka di `src/lib/`. `src/proxy.ts` menerapkan CSP dengan nonce per request; halaman dirender secara dinamis agar nonce pada script sesuai dengan header respons.

Layout root memakai shell dashboard dengan sidebar. Route `/` menyediakan ringkasan dan tiga grafik; `/analysis`, `/dataset`, `/topics`, serta `/evaluation` memuat fitur masing-masing. `usePathname` menentukan menu aktif. Pada layar kecil, sidebar dibuka sebagai dialog native. `ModelHealthProvider` berbagi status model antara ringkasan dan analisis tanpa memuat ulang shell pada setiap navigasi.

Grafik proporsi dan perbandingan split menggunakan `/api/summary`, sedangkan grafik jumlah topik menggunakan `/api/topics?source=trained|notebook`. Sumber topik diteruskan ke halaman detail melalui `/topics?source=...`. Grafik dibuat dengan SVG/HTML/CSS; label, angka, dan tabel alternatif tersedia tanpa dependensi grafik tambahan.

`server/security.py` membatasi frekuensi prediksi dan menyiapkan sel CSV untuk ekspor. API menolak Origin yang tidak diizinkan dan hanya menerima Host yang dikonfigurasi. Pemuatan model serving memerlukan safetensors lokal dan tidak mengizinkan kode remote.

## Direktori lokal

`node_modules/`, `.next/`, `.venv/`, `.cache/`, bytecode Python, model, dan laporan hasil eksekusi dikecualikan dari version control. Instal dependensi frontend dengan lockfile yang disertakan. Tidak perlu memindahkan atau membuat ulang environment yang sudah ada.

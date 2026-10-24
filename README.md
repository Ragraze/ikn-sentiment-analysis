# IKN Sentiment Lab

Dashboard penelitian opini tentang Ibu Kota Nusantara. Next.js menampilkan eksplorasi dataset, klasifikasi sentimen IndoBERT, evaluasi model, dan hasil pemodelan topik Top2Vec melalui API Flask.

Analisis kalimat menggabungkan sentimen IndoBERT dengan topik terdekat dari model Top2Vec per sentimen. Hasil mencakup kata kunci, kemiripan cosine, dan topik pembanding. Model Top2Vec perlu dilatih sekali melalui [panduan pemodelan topik](dashboard/README.md#topic-modelling-top2vec); hasil notebook tetap bisa dibaca sebelum model tersebut terpasang.

## Struktur

```text
data/          Dataset mentah, hasil preprocessing, kamus, prediksi historis
notebooks/     Notebook penelitian beserta output aslinya
dashboard/     Frontend, backend, skrip, pengujian, model, laporan
```

Lihat [keterangan data](data/README.md) dan [urutan notebook](notebooks/README.md).

## Jalankan

Backend pada terminal pertama:

```bash
cd dashboard
bash scripts/setup_backend.sh
.venv/bin/python run.py
```

Frontend pada terminal kedua:

```bash
cd dashboard/frontend
npm ci
npm run dev
```

Buka **http://localhost:3000**. Flask berjalan di **http://127.0.0.1:5000**. Jika dependensi sudah terpasang, cukup jalankan backend dan frontend. Checkpoint lokal berada di `dashboard/models/indobert-ikn/`.

Dari folder utama, `make backend` dan `make frontend` menjalankan kedua layanan pada terminal terpisah. `make test` menjalankan pengujian backend dan frontend, sedangkan `make build` membuat build frontend produksi. Gunakan `make PYTHON=python3 test-backend` untuk interpreter lain yang sudah memiliki dependensi.

[Panduan aplikasi](dashboard/README.md) menjelaskan instalasi manual, impor checkpoint Colab, training, evaluasi, Top2Vec, dan konfigurasi environment.

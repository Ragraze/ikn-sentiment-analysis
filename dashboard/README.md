# IKN Sentiment Lab: Next.js + Flask + IndoBERT + Top2Vec

Dashboard dan API Python yang diadaptasi dari ketiga notebook di folder `../notebooks/`:

1. `Preprocessing_Datasets_IKN.ipynb`: cleaning, tokenisasi, penghapusan slang/stopword/kata Inggris, dan stemming Sastrawi.
2. `Sentimen_Analysis_IKN_IndoBERT.ipynb`: fine-tuning dan evaluasi IndoBERT untuk tiga sentimen.
3. `Topic_Modelling_of_IKN.ipynb`: Top2Vec per sentimen dan coherence score.

Frontend **Next.js App Router + React + TypeScript** meminta data dan prediksi ke backend **Flask**. Next.js meneruskan request `/api/*` ke Flask, sehingga browser menggunakan satu origin tanpa konfigurasi CORS tambahan. Klasifikasi memakai PyTorch/IndoBERT; topic modelling memakai Top2Vec.

## Jalankan

Gunakan Python 3.11 atau 3.12, Node.js >= 20.9, dan koneksi internet untuk instalasi dependensi serta unduhan awal model/resource.

Untuk Linux/WSL, instalasi backend dapat dijalankan dengan satu perintah:

```bash
cd dashboard
bash scripts/setup_backend.sh
.venv/bin/python run.py
```

Skrip menyiapkan virtual environment, pip, PyTorch CPU, dependensi backend, dan resource NLTK. Setelah instalasi, skrip menjalankan tes serta mencoba prediksi checkpoint lokal melalui test client Flask tanpa membuka port. Skrip berhenti jika salah satu tahap gagal. Python 3.10 juga didukung; pilih interpreter dengan `IKN_SETUP_PYTHON=python3.12 bash scripts/setup_backend.sh`. Unduhan memerlukan akses ke PyPI, `download.pytorch.org`, dan server resource NLTK. Skrip dapat dijalankan ulang untuk melanjutkan instalasi yang terputus.

Untuk instalasi manual, gunakan langkah berikut.

Terminal pertama, jalankan backend:

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/setup_nltk.py
python run.py
```

Terminal kedua, jalankan frontend:

```bash
cd dashboard/frontend
npm ci
npm run dev
```

Buka **http://localhost:3000** untuk dashboard. Backend API berjalan pada **http://127.0.0.1:5000**. Pada Windows, aktivasi virtual environment dengan `.venv\Scripts\activate`.

Navigasi utama menggunakan sidebar dengan lima halaman:

| Halaman | Alamat | Isi |
| --- | --- | --- |
| Dashboard | `/` | Ringkasan dataset, donat proporsi sentimen, batang per bagian data, jumlah topik, dan status model |
| Analisis kalimat | `/analysis` | Masukan opini serta hasil sentimen dan topik |
| Dataset opini | `/dataset` | Pencarian, filter, pagination, dan ekspor CSV |
| Pemodelan topik | `/topics` | Kata kunci, bobot, dan coherence; sumber awal hasil training proyek |
| Evaluasi model | `/evaluation` | Metrik klasifikasi dan confusion matrix |

Pada layar kecil, tombol **Menu** membuka sidebar yang dapat ditutup dengan tombol tutup, Escape, atau klik di luar panel. Grafik dashboard menggunakan data asli API. Filter bagian data memperbarui proporsi sentimen; pilihan sumber topik ikut dibawa saat membuka detail. Tabel pada grafik perbandingan menyediakan angka tepat untuk setiap batang.

Pada halaman analisis, **Ctrl/Cmd + Enter** menjalankan analisis, **Salin hasil** menyalin kalimat dan ringkasan hasil, serta **Urungkan** memulihkan kalimat yang dikosongkan. Isian dan hasil terakhir bertahan selama berpindah menu dalam aplikasi, lalu kosong saat halaman dimuat ulang. Tombol **Batalkan** membatalkan request dan tampilan hasil di browser; komputasi yang sudah diterima backend dapat tetap berjalan.

Dataset menyediakan reset filter serta pilihan 8/16/32/50 opini per halaman. Ekspor dan pagination menunggu pencarian/filter selesai agar hasil yang diunduh sesuai dengan tampilan. Halaman evaluasi memiliki penjelasan sumber dan bagian **Cara membaca metrik evaluasi** yang bisa dibuka bila diperlukan.

Untuk produksi frontend: `npm run build` kemudian `npm start`. Ubah URL backend dengan menyalin `frontend/.env.example` menjadi `frontend/.env.local` dan mengisi `FLASK_API_URL`. Restart Next.js setelah mengubah konfigurasi; lakukan build ulang untuk produksi.

Training dijalankan sekali. Untuk pemakaian berikutnya, jalankan backend dan frontend tanpa mengulang training. Ringkasan data dan hasil lama notebook bisa dibuka sebelum checkpoint tersedia. Kolom prediksi menunjukkan status model yang sebenarnya.

Jika checkpoint belum tersedia, jalankan dari folder `dashboard` setelah instalasi:

```bash
python scripts/setup_nltk.py
python scripts/train.py
python scripts/evaluate.py
```

Jika sudah memiliki hasil training Colab, gunakan langkah ekspor di bawah tanpa melatih ulang.

Checkpoint Colab dari `models/indobert_model_3e6.zip` sudah dipasang di **`models/indobert-ikn/`**, sesuai lokasi default backend. Model ini tidak memerlukan training ulang untuk dipakai. Instal dependensi dan resource NLTK, kemudian jalankan backend serta frontend.

## Memasang ZIP hasil Colab

Untuk pemasangan baru ke folder tujuan yang masih kosong:

```bash
python scripts/import_checkpoint.py models/indobert_model_3e6.zip
```

Skrip mengekstrak checkpoint, memeriksa struktur safetensors dan classifier tiga kelas, lalu membuat konfigurasi serving. Label generik `LABEL_0`, `LABEL_1`, `LABEL_2` di ZIP dipetakan menggunakan notebook: **positive=0, neutral=1, negative=2**. Nilai `_num_labels` lama dirapikan berdasarkan shape classifier yang benar-benar tersimpan.

ZIP menyimpan vocabulary dalam `tokenizer.json`. Skrip menulis `vocab.txt` dari indeks yang sama untuk kompatibilitas `BertTokenizer`. Bobot model dan arsip sumber tidak diubah. Konfigurasi asli disimpan sebagai `config.original.json`, dan checksum serta hasil pemeriksaan tersedia di `import_metadata.json`.

Folder yang sudah berisi checkpoint tidak ditimpa oleh skrip impor. Gunakan `--output models/model-lain` untuk memasang checkpoint berbeda, lalu isi `INDOBERT_MODEL_DIR` sesuai lokasi tersebut dan restart backend.

Pretrained IndoBERT tetap merupakan backbone; ZIP yang dipasang harus berisi classifier hasil fine-tuning. Jika belum mempunyai checkpoint, gunakan skrip training atau langkah ekspor runtime notebook di bawah.

## Konfigurasi yang diambil dari notebook

Sumber konfigurasi dapat diperiksa di `config/notebook.json`.

| Parameter | Nilai notebook utama |
| --- | --- |
| Backbone | `indobenchmark/indobert-base-p1` |
| Model | `BertForSequenceClassification` dari Transformers |
| Tokenizer | `BertTokenizer` |
| Indeks label | `0: positive`, `1: neutral`, `2: negative` |
| Optimizer | `torch.optim.Adam` |
| Learning rate | `3e-6` |
| Epoch | `5` |
| Batch size | `32` |
| Maksimum sequence | `512` |
| Random seed | `42` |
| Input training | TSV hasil preprocessing |

Skrip training memindahkan primary run notebook ke CLI, dengan train/validation loop yang sama dan checkpoint pada epoch terakhir. Test tidak digunakan untuk memilih parameter. Notebook juga berisi percobaan learning rate dan epoch lain; parameter dapat diubah lewat argumen CLI.

```bash
python scripts/train.py --learning-rate 2e-6 --epochs 5
python scripts/train.py --batch-size 8 --device cuda
python scripts/train.py --help
```

Default perangkat training adalah CUDA jika tersedia, atau CPU. Default worker adalah 0 agar portabel; `--workers 16` tersedia seperti notebook. CPU dapat membutuhkan waktu jauh lebih lama. Mengganti batch size mengubah proses training dan tidak menjamin hasil numerik yang sama.

Model yang sudah ada tidak ditimpa kecuali memakai `--overwrite`. Cache pretrained dan resource NLTK disimpan di `.cache/` dalam folder dashboard. `--local-files-only` tersedia untuk backbone yang sudah diunduh.

## Kesamaan preprocessing dan tokenisasi

Dataset untuk training dan evaluasi dibaca langsung dari TSV proyek, tanpa preprocessing ulang:

| Bagian | CSV asli untuk eksplorasi | TSV input IndoBERT |
| --- | ---: | ---: |
| Train | 7.512 | 7.498 |
| Validation | 2.504 | 2.502 |
| Test | 2.504 | 2.501 |

Kalimat baru dari dashboard melewati fungsi preprocessing yang dipindahkan dari notebook, kemudian tokenizer IndoBERT. Evaluasi TSV melewati tokenizer saja agar teks tidak diproses dua kali.

Adapter tokenisasi mengikuti `DocumentSentimentDataLoader` IndoNLU: `tokenizer.encode` dengan special token, ambil prefix sampai 512 token, padding ID 0, dan attention mask. Ini mempertahankan perilaku pemotongan notebook untuk kalimat panjang, termasuk kemungkinan terpotongnya token `[SEP]` terakhir. Training dan serving menggunakan adapter yang sama.

Pipeline preprocessing lama menghapus kata slang, stopword, serta kata Inggris. Perilaku ini dipertahankan agar konsisten dengan dataset training. Konsekuensinya, sebagian informasi sentimen dapat hilang. Perubahan preprocessing harus disertai pembuatan dataset dan fine-tuning ulang.

## Ekspor dari runtime notebook yang sudah dilatih

Jika model hasil training masih ada di runtime Colab, tidak perlu melatih ulang. Tambahkan folder kode dashboard ke Python path, lalu jalankan **setelah run training yang ingin dipakai**:

```python
import sys
sys.path.insert(0, '/content/dashboard')  # Sesuaikan lokasi kode dashboard.
from notebook_export import export_checkpoint

export_checkpoint(
    model,
    tokenizer,
    '/content/indobert-ikn',
    id2label=i2w,
)
```

Salin seluruh folder hasil ekspor ke `dashboard/models/indobert-ikn/`. Nama `model`, `tokenizer`, dan `i2w` memang digunakan notebook asli. Varian backbone, preprocessing, dan panjang token default sudah sesuai notebook.

Variabel `model` ditimpa pada setiap skenario tuning notebook. Ekspor tepat setelah skenario yang dipilih, sebelum menjalankan skenario berikutnya. Hasil export meliputi `config.json`, `model.safetensors`, tokenizer, dan `serving.json`.

Backend menggunakan file lokal, memeriksa urutan label serta kelengkapan bobot classifier, lalu menjalankan `model.eval()` dan `torch.inference_mode()`. Tidak ada unduhan model selama request prediksi. Restart backend setelah mengganti checkpoint.

## Evaluasi dan hasil notebook

Halaman evaluasi menggunakan **hasil notebook (CSV)** yang dihitung ulang dari `test_with_predictions new.csv`, sebanyak 2.501 opini. Akurasi **77,61%**, dengan Macro F1 **0,6393**. Sumber ini ditetapkan langsung pada halaman, tanpa pilihan sumber evaluasi. Angka berasal dari prediksi penelitian yang tersimpan.

Perintah `python scripts/evaluate.py` menghasilkan laporan evaluasi checkpoint dan CSV prediksi untuk pipeline pemodelan topik.

Output evaluasi checkpoint:

```text
reports/test.json                  # Akurasi, macro F1, confusion matrix, metrik per kelas.
reports/test_with_predictions.csv  # text, sentiment, sentiment_predict; input untuk notebook Top2Vec.
```

Perbaikan dari notebook: `classification_report(..., target_names=w2i.keys())` tanpa `labels` eksplisit dapat menukar nama positif/negatif karena urutan alfabet kelas berbeda dari urutan IndoNLU. Perhitungan dashboard menggunakan urutan eksplisit **positive → neutral → negative**. Support aktual pada TSV test: positif 388, netral 366, negatif 1.747.

`test_with_predictions_and_coherence.csv` menyimpan prediksi yang berbeda dari CSV pertama. Panel topik menggunakan output yang benar-benar tersimpan di notebook Top2Vec dan menjelaskan sumbernya.

## Topic modelling Top2Vec

Bagian topic modelling termasuk dalam frontend Next.js, dengan:

- Pilihan sentimen positif, netral, dan negatif.
- Kata pembentuk setiap topik.
- Perbandingan coherence score `c_v` ketiga sentimen.
- Pilihan sumber **Hasil notebook** atau **Hasil training proyek**.

Sumber notebook membaca output `../notebooks/Topic_Modelling_of_IKN.ipynb`. Untuk menjalankan ulang pipeline pemodelan topik dari CSV prediksi IndoBERT:

```bash
python -m pip install -r requirements-topics.txt
python scripts/setup_nltk.py
python scripts/evaluate.py
python scripts/train_topics.py
```

Skrip mengikuti notebook: satu Top2Vec untuk setiap sentimen, embedding `doc2vec`, `speed='deep-learn'`, `min_count=10`, serta evaluasi gensim `CoherenceModel(coherence='c_v')`. Model disimpan di `models/top2vec/`, sedangkan laporan, jumlah opini per topik, dan bobot kata berada di `reports/topics.json`. Setiap kelompok sentimen memerlukan sedikitnya 20 dokumen; korpus yang kecil atau kurang beragam tetap dapat gagal membentuk cluster. Top2Vec menentukan jumlah topik dari korpus.

Jika ingin menggunakan CSV prediksi yang sudah tersedia tanpa menjalankan IndoBERT ulang:

```bash
python scripts/train_topics.py --predictions "../data/predictions/test_with_predictions_and_coherence.csv"
```

Restart backend setelah training atau mengganti model. Buka **Analisis kalimat**: IndoBERT mengklasifikasikan sentimen, lalu `Top2Vec.query_topics` mencocokkan teks hasil preprocessing ke model untuk sentimen tersebut. UI menampilkan topik terdekat, sepuluh kata kunci, kemiripan cosine, jumlah opini dalam topik, dan hingga dua topik pembanding. Nomor topik berlaku di dalam masing-masing kelompok sentimen. Judul topik memakai kata kunci model, tanpa nama kategori buatan.

Model dimuat saat diperlukan dan disimpan dalam memori per proses; training tidak berjalan dalam request. Kalimat tanpa kata yang dikenali korpus tidak diberi topik acak. Jika model topik belum tersedia atau gagal dimuat, respons sentimen tetap berhasil dan bagian topik menjelaskan statusnya. Laporan notebook tidak digunakan sebagai pengganti model inferensi.

Kemiripan topik adalah cosine pada rentang −1 sampai 1, bukan probabilitas atau confidence sentimen. Hasil terdekat juga belum tentu relevan, terutama untuk kalimat pendek atau di luar konteks IKN. Coherence c_v mengukur keterkaitan kata pada korpus, bukan skor untuk kalimat baru. Kata kunci pada panel laporan menampilkan bobot cosine terhadap topik ketika bobot tersedia.

Perintah lain yang tersedia:

```bash
python scripts/train_topics.py --help
python scripts/train_topics.py --workers 2 --speed learn
```

Mengganti `--speed` mengubah pelatihan dari konfigurasi notebook. `--overwrite` diperlukan untuk mengganti artefak model yang sudah ada. Hanya muat artefak Top2Vec lokal yang dibuat atau dipercaya pengelola; format penyimpanannya memakai deserialisasi Python.

Kontrak API:

- `GET /api/health`: status IndoBERT dan `topics.groups` untuk tiga model Top2Vec, tanpa memuat bobot.
- `POST /api/predict` dengan JSON `{"text":"Opini tentang IKN"}`: hasil sentimen ditambah `topic_analysis` (`available`, `matched`, `state`, `sentiment`, `topics`, `message`). Setiap topik memiliki `number` (mulai 0), `words`, `word_scores`, `similarity`, dan `documents`.
- `GET /api/topics?source=notebook|trained`: laporan topik per sentimen. Pilih **Hasil training proyek** untuk melihat hasil pelatihan baru.

Implementasi pencocokan mengikuti [API resmi Top2Vec: query_topics](https://top2vec.readthedocs.io/en/stable/api.html#top2vec.Top2Vec.query_topics).

## Struktur aplikasi

```text
dashboard/
  frontend/           # Next.js App Router, React, TypeScript
    src/
      app/
      features/
      components/
      hooks/
      lib/
    tests/
  server/             # Flask API, IndoBERT inference, dataset, hasil Top2Vec
  scripts/            # Training/evaluasi IndoBERT dan Top2Vec
  config/             # Konfigurasi yang diambil dari notebook
  models/             # Checkpoint IndoBERT dan model Top2Vec
  reports/            # Evaluasi, prediksi CSV, dan laporan topik
  run.py              # Entrypoint Flask
```

Folder checkpoint IndoBERT berada di `models/indobert-ikn/`.

Beberapa output eksperimen learning rate di notebook tidak cocok dengan source cell yang tersimpan. Konfigurasi training aplikasi memakai source primary run (`3e-6`, 5 epoch), dan metrik lama dihitung dari CSV aktual.

## Environment variables

| Variabel | Default | Fungsi |
| --- | --- | --- |
| `INDOBERT_MODEL_DIR` | `dashboard/models/indobert-ikn` | Checkpoint terlatih |
| `IKN_DATA_DIR` | `data/` di folder utama proyek | Subfolder `raw/`, `processed/`, `external/`, dan `predictions/` |
| `IKN_NOTEBOOKS_DIR` | `notebooks/` di folder utama proyek | Notebook asli dan output topik tersimpan |
| `INDOBERT_DEVICE` | `cpu` | Perangkat serving: `cpu` atau `cuda` |
| `TOP2VEC_MODEL_DIR` | `dashboard/models/top2vec` | Tiga model Top2Vec lokal; juga dipakai CLI training |
| `TOP2VEC_REPORT_DIR` | `dashboard/reports` | Laporan `topics.json`; juga dipakai CLI training |
| `PORT` | `5000` | Port Flask lokal |
| `FRONTEND_URL` | `http://localhost:3000` | Origin frontend yang diizinkan melakukan prediksi |
| `IKN_TRUSTED_HOSTS` | `localhost,127.0.0.1,[::1]` | Daftar Host backend yang diterima, dipisahkan koma |
| `FLASK_API_URL` | `http://127.0.0.1:5000` | URL Flask pada konfigurasi proxy Next.js |

## Pengujian

```bash
python -m unittest discover -s tests -v
cd frontend
npm run typecheck
npm test
npm run build
npm run test:render
```

Tes memeriksa data asli, output notebook, urutan label, cleaning, pemotongan token IndoNLU, metrik CSV, kontrak API Flask, laporan topik, dan proxy/request frontend. Pengujian integrasi topik memakai test double dengan kontrak Top2Vec untuk memeriksa pemilihan model, caching, kosakata asing, cosine tidak valid, dan hasil sentimen saat Top2Vec tidak tersedia. Tes rendering komponen memeriksa hasil topik, fallback, escaping, dan perbedaan cosine dengan persentase. Tes API membutuhkan Flask terpasang. Verifikasi training dan inferensi Top2Vec sungguhan membutuhkan dependensi serta artefak model.

`test:render` memeriksa rendering produksi kelima halaman, menu sidebar aktif, pemisahan konten, pilihan sumber topik, nonce CSP per halaman, nonce script, serta header tanpa membuka port jaringan. Jalankan setelah build. Pengujian ini tidak menggantikan pemeriksaan visual dan interaksi di browser.

Prediksi berjalan setelah tombol **Analisis kalimat** ditekan, dengan batas 2.000 karakter, satu inferensi aktif per proses backend, dan 30 percobaan per menit per proses. Request berlebih menerima HTTP 429; model yang sedang sibuk menerima HTTP 503. Kedua respons menyertakan `Retry-After`.

Frontend mengikuti tema sistem. Aksen warna dibatasi pada tindakan utama dan kategori data.

## Referensi

- [Source IndoNLU: dataset dan data loader](https://github.com/IndoNLP/indonlu/blob/master/utils/data_utils.py)
- [Panduan fine-tuning IndoNLU](https://github.com/IndoNLP/indonlu/wiki/Quickstart-~-Fine-Tune)
- [Pretrained IndoBERT base p1](https://huggingface.co/indobenchmark/indobert-base-p1)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Next.js API rewrites](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites)
- [Top2Vec](https://github.com/ddangelov/Top2Vec)

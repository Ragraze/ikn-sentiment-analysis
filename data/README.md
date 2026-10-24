# Data penelitian IKN

File sumber dipertahankan dengan nama dan isi aslinya agar dapat ditelusuri ke notebook.

| Folder | Isi | Digunakan oleh |
| --- | --- | --- |
| `raw/` | CSV train, validation, dan test berlabel | Eksplorasi dan distribusi sentimen |
| `processed/` | TSV hasil preprocessing | Training dan evaluasi IndoBERT |
| `external/` | Kamus slang dan stopword bahasa Indonesia | Preprocessing kalimat baru |
| `predictions/` | CSV prediksi tersimpan dari notebook | Evaluasi historis dan input Top2Vec |

Hasil yang dihasilkan aplikasi disimpan di `dashboard/reports/`, terpisah dari data sumber. Checkpoint disimpan di `dashboard/models/`.

`IKN_DATA_DIR` dapat diarahkan ke direktori data lain dengan struktur yang sama. Direktori datar dari integrasi lama masih didukung. Notebook ditentukan secara terpisah melalui `IKN_NOTEBOOKS_DIR`.

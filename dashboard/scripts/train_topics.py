"""Port Top2Vec training and c_v coherence from Topic_Modelling_of_IKN.ipynb."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from server.topics import LABELS


def load_documents(source):
    with source.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {'text', 'sentiment_predict'}.issubset(reader.fieldnames):
            raise ValueError('CSV harus memiliki kolom text dan sentiment_predict seperti notebook.')
        groups = {label: [] for label in LABELS}
        for index, row in enumerate(reader, 2):
            label = row['sentiment_predict']
            if label not in groups or not isinstance(row['text'], str) or not row['text'].strip():
                raise ValueError(f'Label atau teks tidak valid pada baris {index}.')
            groups[label].append(row['text'])
    if any(len(documents) < 20 for documents in groups.values()):
        raise ValueError('Setiap sentimen memerlukan minimal 20 dokumen untuk UMAP dan HDBSCAN Top2Vec.')
    return groups


def main():
    parser = argparse.ArgumentParser(description='Latih Top2Vec per sentimen dan hitung coherence c_v sesuai notebook.')
    parser.add_argument('--predictions', default=str(APP / 'reports/test_with_predictions.csv'))
    parser.add_argument('--model-dir', default=os.environ.get('TOP2VEC_MODEL_DIR', str(APP / 'models/top2vec')))
    parser.add_argument('--report-dir', default=os.environ.get('TOP2VEC_REPORT_DIR', str(APP / 'reports')))
    parser.add_argument('--min-count', type=int, default=10)
    parser.add_argument('--speed', choices=['fast-learn', 'learn', 'deep-learn'], default='deep-learn')
    parser.add_argument('--workers', type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    source, model_dir = Path(args.predictions), Path(args.model_dir)
    if args.min_count < 1 or args.workers < 1:
        parser.error('--min-count dan --workers harus positif.')
    if not source.is_file():
        parser.error('CSV prediksi belum ada. Jalankan scripts/evaluate.py atau isi --predictions dengan CSV hasil notebook.')
    if model_dir.exists() and any(model_dir.iterdir()) and not args.overwrite:
        parser.error('Folder Top2Vec sudah berisi file. Pilih folder lain atau gunakan --overwrite.')
    try:
        groups = load_documents(source)
    except ValueError as error:
        parser.error(str(error))
    try:
        import nltk
        from nltk.tokenize import word_tokenize
        from top2vec import Top2Vec
        from gensim.corpora import Dictionary
        from gensim.models import CoherenceModel
    except ImportError:
        parser.error('Dependensi Top2Vec belum lengkap. Jalankan python -m pip install -r requirements-topics.txt dari folder dashboard.')
    nltk.data.path.insert(0, str(APP / '.cache/nltk'))
    word_tokenize('periksa resource tokenizer')
    results = {}
    model_dir.mkdir(parents=True, exist_ok=True)
    for label in LABELS:
        documents = groups[label]
        print(f'Training Top2Vec {label}: {len(documents)} dokumen', flush=True)
        model = Top2Vec(documents, embedding_model='doc2vec', speed=args.speed,
                        min_count=args.min_count, workers=args.workers)
        words, scores, numbers = model.get_topics()
        sizes, size_numbers = model.get_topic_sizes()
        counts = {int(number): int(size) for number, size in zip(size_numbers, sizes)}
        tokens = [word_tokenize(document.lower()) for document in documents]
        dictionary = Dictionary(tokens)
        coherence = CoherenceModel(topics=[list(topic) for topic in words], texts=tokens,
                                   dictionary=dictionary, coherence='c_v', processes=1).get_coherence()
        if not math.isfinite(coherence):
            raise ValueError(f'Coherence {label} tidak valid; periksa jumlah dokumen dan kata pada korpus.')
        model.save(str(model_dir / f'model_top2vec_{label}'))
        results[label] = dict(documents=len(documents), coherence=float(coherence),
                             topics=[dict(number=int(number), words=list(topic), word_scores=[float(score) for score in weights],
                                          documents=counts[int(number)])
                                     for number, topic, weights in zip(numbers, words, scores)])
        print(f'{label}: {len(numbers)} topik; coherence={coherence:.4f}', flush=True)
    report = dict(algorithm='Top2Vec', source_file=source.name,
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  trained_at=datetime.now(timezone.utc).isoformat(),
                  parameters=dict(embedding_model='doc2vec', speed=args.speed, min_count=args.min_count,
                                  workers=args.workers, coherence='c_v'), groups=results)
    output = Path(args.report_dir) / 'topics.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2))
    temporary.replace(output)
    print(f'Hasil pemodelan topik tersimpan: {output}')


if __name__ == '__main__':
    main()

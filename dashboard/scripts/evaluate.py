"""Evaluate the installed IndoBERT checkpoint on the notebook's preprocessed test TSV."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from server.data import DatasetRepository
from server.inference import IndoBertService
from server.metrics import calculate_metrics
from server.settings import DATA_DIR


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', default=os.environ.get('INDOBERT_MODEL_DIR', str(APP / 'models/indobert-ikn')))
    parser.add_argument('--data-dir', default=str(DATA_DIR))
    parser.add_argument('--device', default=os.environ.get('INDOBERT_DEVICE', 'cpu'))
    parser.add_argument('--batch-size', type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 128:
        parser.error('--batch-size harus 1–128.')
    data = DatasetRepository(Path(args.data_dir))
    model = IndoBertService(Path(args.model_dir), args.device, Path(args.data_dir))
    model._load()
    preprocessed = model.manifest['preprocessing'] == 'notebook'
    rows = data.preprocessed('test') if preprocessed else data.filter(split='test')
    predictions = []
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start:start + args.batch_size]
        predictions.extend(model.predict_many([row['text'] for row in batch], preprocessed=preprocessed))
        print(f'Evaluasi {min(start + args.batch_size, len(rows))}/{len(rows)}', flush=True)
    report = calculate_metrics([row['label'] for row in rows], [result['label'] for result in predictions])
    report.update(model='IndoBERT', base_model=model.manifest['base_model'], split='test',
                  model_fingerprint=model.fingerprint(), evaluated_at=datetime.now(timezone.utc).isoformat(),
                  preprocessing=model.manifest['preprocessing'], max_length=model.manifest['max_length'],
                  source='checkpoint', dataset='preprocessed_final_ikn_test.tsv' if preprocessed else 'final_ikn_test_602020.csv')
    target = APP / 'reports/test.json'
    target.parent.mkdir(exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2))
    temporary.replace(target)
    # This is the same text/label interface consumed by the original Top2Vec notebook.
    import csv
    with (APP / 'reports/test_with_predictions.csv').open('w', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=['text', 'sentiment', 'sentiment_predict'])
        writer.writeheader()
        for row, prediction in zip(rows, predictions):
            writer.writerow(dict(text=prediction['normalized'], sentiment=row['label'], sentiment_predict=prediction['label']))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

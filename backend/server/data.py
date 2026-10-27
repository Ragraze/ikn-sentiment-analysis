"""Read datasets and saved research outputs."""
from collections import Counter
import csv
from functools import cached_property
import json
from pathlib import Path
import re
from .settings import DATA_DIR, NOTEBOOK, NOTEBOOKS_DIR, data_file
from .metrics import calculate_metrics

LABELS = ('negative', 'neutral', 'positive')


class DatasetRepository:
    def __init__(self, root: Path = DATA_DIR, notebooks_dir: Path = NOTEBOOKS_DIR):
        self.root = Path(root)
        self.notebooks_dir = Path(notebooks_dir)

    @cached_property
    def rows(self):
        result = []
        for split in ('train', 'val', 'test'):
            path = data_file(self.root, 'raw', f'final_ikn_{split}_602020.csv')
            with path.open(encoding='utf-8-sig', newline='') as source:
                for index, row in enumerate(csv.DictReader(source), 1):
                    if row['label'] not in LABELS:
                        raise ValueError('Label dataset tidak dikenali.')
                    result.append(dict(id=f'{split}-{index}', split=split, text=row['text'], label=row['label']))
        return result

    def filter(self, query='', split='all', label='all'):
        query = query.casefold()
        return [row for row in self.rows if (split == 'all' or row['split'] == split)
                and (label == 'all' or row['label'] == label) and query in row['text'].casefold()]

    def preprocessed(self, split):
        filename = NOTEBOOK['datasets'][split]
        with data_file(self.root, 'processed', filename).open(encoding='utf-8-sig', newline='') as source:
            rows = []
            for index, row in enumerate(csv.reader(source, delimiter='\t'), 1):
                if len(row) != 2 or not row[0].strip() or row[1] not in LABELS:
                    raise ValueError(f'Baris TSV tidak valid pada {filename}:{index}.')
                rows.append(dict(text=row[0], label=row[1], split=split, id=f'preprocessed-{split}-{index}'))
            return rows

    def notebook_evaluation(self):
        filename = 'test_with_predictions new.csv'
        path = data_file(self.root, 'predictions', filename)
        if not path.is_file():
            return dict(available=False, message='CSV hasil prediksi notebook belum tersedia.')
        with path.open(encoding='utf-8-sig', newline='') as source:
            rows = list(csv.DictReader(source))
        metrics = calculate_metrics([row['sentiment'] for row in rows], [row['sentiment_predict'] for row in rows])
        return dict(available=True, source='notebook_csv', source_file=filename,
                    message='Dihitung ulang dari CSV prediksi yang tersimpan; belum memverifikasi checkpoint backend.', **metrics)

    @cached_property
    def _summary(self):
        counts = Counter(row['label'] for row in self.rows)
        splits = {}
        for split in ('train', 'val', 'test'):
            items = self.filter(split=split)
            split_counts = Counter(row['label'] for row in items)
            splits[split] = dict(count=len(items), counts={label: split_counts[label] for label in LABELS})
        processed_counts = {split: len(self.preprocessed(split)) for split in ('train', 'val', 'test')}
        return dict(total=len(self.rows), counts={label: counts[label] for label in LABELS},
                    splits=splits, preprocessed=processed_counts, notebook=NOTEBOOK, topics=self.topics())

    def summary(self):
        return self._summary

    def topics(self):
        source = self.notebooks_dir / 'Topic_Modelling_of_IKN.ipynb'
        if not source.is_file():
            return dict(available=False, source=None, groups={})
        notebook = json.loads(source.read_text(encoding='utf-8'))
        groups = {label: dict(topics=[], coherence=None) for label in LABELS}
        for cell in notebook.get('cells', []):
            code = ''.join(cell.get('source', []))
            outputs = ''.join(''.join(output.get('text', [])) for output in cell.get('outputs', []))
            for label in LABELS:
                if re.search(rf'#\s*{label.upper()} TOPIC', code):
                    for number, words in re.findall(r'Aspek (\d+): ([^\n]+)', outputs):
                        groups[label]['topics'].append(dict(number=int(number), words=words.split(', ')))
            for label, score in re.findall(r'Coherence Score untuk (Positive|Neutral|Negative): ([0-9.]+)', outputs):
                groups[label.lower()]['coherence'] = float(score)
        return dict(available=any(group['topics'] for group in groups.values()), source=source.name, groups=groups)

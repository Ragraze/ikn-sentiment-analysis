"""Read topic reports and match new sentences with locally trained Top2Vec models."""
import importlib.util
import json
import math
import logging
from pathlib import Path
import threading

LABELS = ('positive', 'neutral', 'negative')


class Top2VecService:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self._models = {}
        self._vocabularies = {}
        self._errors = set()
        self._lock = threading.RLock()

    def _path(self, label):
        return self.model_dir / f'model_top2vec_{label}'

    def status(self):
        groups = {}
        for label in LABELS:
            if not self._path(label).is_file():
                state = 'missing_checkpoint'
            elif label in self._errors:
                state = 'error'
            elif label in self._models:
                state = 'ready'
            elif importlib.util.find_spec('top2vec') is None:
                state = 'missing_dependency'
            else:
                state = 'configured'
            groups[label] = dict(state=state, available=state in ('ready', 'configured'))
        return dict(model='Top2Vec', available=all(group['available'] for group in groups.values()), groups=groups)

    def _load(self, label):
        if label not in self._models:
            from top2vec import Top2Vec
            model = Top2Vec.load(str(self._path(label)))
            # This application trains Doc2Vec locally, so serving never needs an embedding download.
            if model.embedding_model != 'doc2vec':
                raise ValueError('Model serving Top2Vec harus memakai embedding doc2vec seperti notebook.')
            if model.get_num_topics() < 1:
                raise ValueError('Model Top2Vec tidak memiliki topik.')
            self._vocabularies[label] = set(model.vocab)
            self._models[label] = model
        return self._models[label]

    def predict(self, text, label, limit=3):
        if label not in LABELS:
            raise ValueError('Sentimen untuk pemodelan topik tidak valid.')
        if type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError('Jumlah topik harus antara 1 dan 10.')
        base = dict(model='Top2Vec', sentiment=label, topics=[], matched=False)
        if not self._path(label).is_file():
            return dict(base, available=False, state='missing_checkpoint',
                        message='Model topik untuk sentimen ini belum tersedia. Pengelola perlu melatih Top2Vec terlebih dahulu.')
        with self._lock:
            try:
                from gensim.utils import simple_preprocess
                model = self._load(label)
                self._errors.discard(label)
                tokens = simple_preprocess(text)
                if not any(token in self._vocabularies[label] for token in tokens):
                    return dict(base, available=True, state='no_match',
                                message='Kata dalam kalimat belum dikenali korpus Top2Vec. Coba opini IKN yang lebih lengkap.')
                words, weights, similarities, numbers = model.query_topics(
                    query=text, num_topics=min(limit, model.get_num_topics()))
                if not (len(words) == len(weights) == len(similarities) == len(numbers)) or not len(numbers):
                    raise ValueError('Hasil pencarian topik tidak lengkap.')
                sizes, size_numbers = model.get_topic_sizes()
                counts = {int(number): int(size) for number, size in zip(size_numbers, sizes)}
                topics = []
                for topic_words, scores, similarity, number in zip(words, weights, similarities, numbers):
                    similarity = float(similarity)
                    keyword_scores = [float(score) for score in scores[:10]]
                    keywords = [str(word) for word in topic_words[:10]]
                    if (not math.isfinite(similarity) or not -1.00001 <= similarity <= 1.00001 or
                        not keywords or len(keywords) != len(keyword_scores) or
                        any(not math.isfinite(score) for score in keyword_scores)):
                        raise ValueError('Skor Top2Vec tidak valid.')
                    topics.append(dict(number=int(number), words=keywords, word_scores=keyword_scores,
                                       similarity=max(-1., min(1., similarity)), documents=counts[int(number)]))
                self._errors.discard(label)
                if topics[0]['similarity'] <= 0:
                    return dict(base, available=True, state='no_match',
                                message='Tidak ditemukan topik dengan kemiripan positif. Coba kalimat yang lebih spesifik tentang IKN.')
                return dict(base, available=True, matched=True, state='ready', topics=topics,
                            message='Topik terdekat dalam kategori sentimen hasil IndoBERT.')
            except Exception:
                logging.getLogger(__name__).exception('Top2Vec inference failed for %s', label)
                self._errors.add(label)
                return dict(base, available=False, state='error',
                            message='Top2Vec belum dapat digunakan. Pengelola perlu memeriksa dependensi dan model topik. Hasil sentimen tetap tersedia.')


def empty_topics(message, origin='trained'):
    return dict(available=False, source=None, origin=origin, message=message,
                groups={label: dict(topics=[], coherence=None) for label in LABELS})


def get_topics(repository, report_dir: Path, source='notebook'):
    if source == 'notebook':
        return dict(**repository.topics(), origin='notebook')
    if source != 'trained':
        raise ValueError('Sumber topik harus notebook atau trained.')
    report = report_dir / 'topics.json'
    if not report.is_file():
        return empty_topics('Model Top2Vec proyek belum dilatih. Jalankan python scripts/train_topics.py setelah evaluasi IndoBERT.')
    try:
        data = json.loads(report.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('algorithm') != 'Top2Vec' or set(data['groups']) != set(LABELS):
            raise ValueError('Metadata model atau sentimen tidak sesuai.')
        for group in data['groups'].values():
            if not isinstance(group['topics'], list) or not group['topics']:
                raise ValueError('Daftar topik kosong atau tidak valid.')
            if type(group['coherence']) not in (int, float) or not math.isfinite(group['coherence']):
                raise ValueError('Coherence score tidak valid.')
            if 'documents' in group and (type(group['documents']) is not int or group['documents'] < 1):
                raise ValueError('Jumlah dokumen kelompok tidak valid.')
            for topic in group['topics']:
                if type(topic['number']) is not int or topic['number'] < 0 or not isinstance(topic['words'], list) or not topic['words'] or not all(isinstance(word, str) and word.strip() for word in topic['words']):
                    raise ValueError('Kata pembentuk topik tidak valid.')
                if 'documents' in topic and (type(topic['documents']) is not int or topic['documents'] < 0):
                    raise ValueError('Jumlah dokumen topik tidak valid.')
                scores = topic.get('word_scores')
                if scores is not None and (not isinstance(scores, list) or len(scores) != len(topic['words']) or
                    any(type(value) not in (int, float) or not math.isfinite(value) for value in scores)):
                    raise ValueError('Bobot kata topik tidak valid.')
        return dict(available=True, source=data['source_file'], origin='trained', groups=data['groups'],
                    trained_at=data.get('trained_at'), parameters=data.get('parameters'))
    except (ValueError, KeyError, TypeError, OSError, AttributeError):
        logging.getLogger(__name__).warning('Invalid Top2Vec report', exc_info=True)
        return empty_topics('Laporan Top2Vec tidak valid. Minta pengelola membuat ulang laporan.')

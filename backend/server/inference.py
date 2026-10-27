"""Serve only a locally exported, fine-tuned IndoBERT sequence classifier."""
import hashlib
import json
import logging
import math
from pathlib import Path
import threading

from .preprocessing import Preprocessor
from .tokenization import encode_batch, to_tensors
from .settings import DATA_DIR, NOTEBOOK

LABELS = ('negative', 'neutral', 'positive')
ALIASES = {'negative': 'negative', 'negatif': 'negative', 'neutral': 'neutral',
           'netral': 'neutral', 'positive': 'positive', 'positif': 'positive'}


class ModelUnavailable(RuntimeError):
    pass


def read_manifest(model_dir):
    path = model_dir / 'serving.json'
    if not path.is_file():
        raise ModelUnavailable('Bobot hasil fine-tuning belum tersedia. Jalankan python scripts/train.py, atau ekspor model dan tokenizer dari notebook ke models/indobert-ikn.')
    try:
        manifest = json.loads(path.read_text())
        labels = {int(key): ALIASES[value.lower()] for key, value in manifest['id2label'].items()}
        if set(labels) != {0, 1, 2} or set(labels.values()) != set(LABELS):
            raise ValueError('Mapping label harus memuat tiga sentimen yang berbeda.')
        if manifest['preprocessing'] not in ('raw', 'notebook'):
            raise ValueError('Profil preprocessing tidak dikenali.')
        if manifest.get('tokenization') != 'indonlu-prefix':
            raise ValueError('Gunakan tokenization indonlu-prefix sesuai notebook dan ekspor ulang checkpoint.')
        if not isinstance(manifest['max_length'], int) or not 2 <= manifest['max_length'] <= 512:
            raise ValueError('max_length harus 2–512.')
        if not isinstance(manifest.get('base_model'), str) or not manifest['base_model'].strip() or manifest.get('task') != 'sentiment-classification':
            raise ValueError('Metadata backbone atau task belum lengkap.')
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as error:
        raise ModelUnavailable('Konfigurasi checkpoint tidak valid. Periksa serving.json pada backend.') from error
    return manifest, labels


class IndoBertService:
    def __init__(self, model_dir: Path, device='cpu', data_dir=None):
        self.model_dir = model_dir.resolve()
        self.device = device
        self.data_dir = Path(data_dir) if data_dir is not None else DATA_DIR
        self._lock = threading.RLock()
        self._loaded = False
        self._error = None

    def status(self):
        try:
            manifest, _ = read_manifest(self.model_dir)
        except ModelUnavailable as error:
            return dict(ready=False, state='missing_checkpoint', model='IndoBERT',
                        base_model=NOTEBOOK['base_model'], max_length=NOTEBOOK['max_length'], message=str(error))
        return dict(ready=self._loaded, state='ready' if self._loaded else ('error' if self._error else 'configured'),
                    model='IndoBERT', base_model=manifest['base_model'], preprocessing=manifest['preprocessing'],
                    max_length=manifest['max_length'], message=self._error or ('Model siap.' if self._loaded else 'Checkpoint terpasang. Model akan dimuat saat prediksi pertama.'))

    def _load(self):
        if self._loaded:
            return
        manifest, labels = read_manifest(self.model_dir)
        try:
            import torch
            from transformers import AutoConfig, BertForSequenceClassification, BertTokenizer
            config = AutoConfig.from_pretrained(str(self.model_dir), local_files_only=True, trust_remote_code=False)
            if config.model_type != 'bert' or config.num_labels != 3:
                raise ValueError('Checkpoint harus berupa IndoBERT/BERT untuk klasifikasi tiga sentimen.')
            if {int(key): ALIASES.get(value.lower()) for key, value in config.id2label.items()} != labels:
                raise ValueError('Mapping config.json berbeda dari serving.json; gunakan urutan label dari notebook.')
            tokenizer = BertTokenizer.from_pretrained(str(self.model_dir), local_files_only=True)
            model, info = BertForSequenceClassification.from_pretrained(
                str(self.model_dir), local_files_only=True, trust_remote_code=False, use_safetensors=True,
                output_loading_info=True)
            if info.get('missing_keys') or info.get('mismatched_keys') or info.get('error_msgs'):
                raise ValueError('Bobot classifier belum lengkap. Gunakan checkpoint hasil fine-tuning, bukan backbone pretrained dengan classifier acak.')
            preprocessing = Preprocessor(manifest['preprocessing'], self.data_dir)
            model.to(self.device)
            model.eval()
            self.torch, self.tokenizer, self.model = torch, tokenizer, model
            self.preprocess, self.manifest, self.labels = preprocessing, manifest, labels
            self._loaded = True
            self._error = None
        except (ImportError, OSError, ValueError, LookupError, RuntimeError, TypeError, AttributeError) as error:
            logging.getLogger(__name__).exception('Failed to load local IndoBERT checkpoint')
            self._error = 'Model belum dapat dimuat. Minta pengelola memeriksa checkpoint dan dependensi backend.'
            raise ModelUnavailable(self._error) from error

    def predict_many(self, texts, *, preprocessed=False):
        with self._lock:
            self._load()
            normalized = list(texts) if preprocessed else [self.preprocess(text) for text in texts]
            if any(not text.strip() for text in normalized):
                raise ValueError('Teks kosong setelah preprocessing notebook. Coba kalimat yang lebih lengkap.')
            tokens = to_tensors(self.torch, encode_batch(self.tokenizer, normalized, self.manifest['max_length']), self.device)
            with self.torch.inference_mode():
                scores = self.torch.softmax(self.model(**tokens, return_dict=True).logits, dim=-1).cpu().tolist()
            results = []
            for text, probabilities in zip(normalized, scores):
                if len(probabilities) != 3 or not all(math.isfinite(value) and 0 <= value <= 1 for value in probabilities):
                    raise ModelUnavailable('Model menghasilkan skor yang tidak valid.')
                by_label = {self.labels[index]: probability for index, probability in enumerate(probabilities)}
                label = max(by_label, key=by_label.get)
                results.append(dict(label=label, scores=by_label, confidence=by_label[label], normalized=text,
                                    model='IndoBERT', base_model=self.manifest['base_model']))
            return results

    def predict(self, text):
        return self.predict_many([text])[0]

    def fingerprint(self):
        read_manifest(self.model_dir)
        # Cached per running service; restart after replacing a checkpoint.
        if not hasattr(self, '_fingerprint'):
            digest = hashlib.sha256()
            names = ('serving.json', 'config.json', 'tokenizer.json', 'tokenizer_config.json',
                     'special_tokens_map.json', 'vocab.txt', 'model.safetensors.index.json')
            files = [path for path in self.model_dir.iterdir() if path.is_file() and
                     (path.name in names or path.suffix == '.safetensors')]
            if not any(path.suffix == '.safetensors' for path in files):
                raise ModelUnavailable('File bobot IndoBERT belum tersedia.')
            for path in sorted(files):
                digest.update(path.name.encode())
                with path.open('rb') as source:
                    for block in iter(lambda: source.read(1024 * 1024), b''):
                        digest.update(block)
            self._fingerprint = digest.hexdigest()
        return self._fingerprint

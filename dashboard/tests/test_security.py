import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from server import create_app
from server.inference import IndoBertService, ModelUnavailable
from server.metrics import calculate_metrics
from server.security import RequestBudget


class Predictor:
    def predict(self, text):
        return {'label': 'neutral', 'confidence': 1, 'scores': {'neutral': 1, 'positive': 0, 'negative': 0}}

    def status(self):
        return {'ready': True, 'state': 'ready', 'model': 'IndoBERT'}


class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.config = {'TESTING': True, 'TOPIC_MODEL_DIR': temporary.name, 'TOPIC_REPORT_DIR': temporary.name}
        self.app = create_app(self.config, predictor=Predictor())
        self.client = self.app.test_client()

    def test_cross_site_prediction_and_untrusted_hosts_are_rejected(self):
        for headers in [{'Origin': 'https://other.example'}, {'Origin': 'null'}, {'Sec-Fetch-Site': 'cross-site'}]:
            self.assertEqual(self.client.post('/api/predict', json={'text': 'Opini IKN'}, headers=headers).status_code, 403)
        self.assertEqual(self.client.get('/api/summary', headers={'Host': 'other.example'}).status_code, 400)
        self.assertEqual(self.client.post('/api/predict', json={'text': 'Opini IKN'}, headers={'Origin': 'http://localhost:3000'}).status_code, 200)

    def test_large_or_malformed_input_is_rejected_before_inference(self):
        response = self.client.post('/api/predict', json={'text': 'x' * 20_000})
        self.assertEqual(response.status_code, 413)
        self.assertIsInstance(response.get_json()['error'], str)
        for text in ['teks\x00IKN', 'teks\ud800IKN']:
            self.assertEqual(self.client.post('/api/predict', json={'text': text}).status_code, 400)
        for query in ['q=' + 'a' * 201, 'split=../../etc', 'page=1&page=2', 'page=1000001']:
            self.assertEqual(self.client.get('/api/dataset?' + query).status_code, 400)

    def test_prediction_budget_returns_retry_after(self):
        client = create_app({**self.config, 'PREDICTION_LIMIT': 1}, predictor=Predictor()).test_client()
        self.assertEqual(client.post('/api/predict', json={'text': 'Opini IKN'}).status_code, 200)
        response = client.post('/api/predict', json={'text': 'Opini IKN'})
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers['Retry-After']), 0)

    def test_parallel_prediction_does_not_create_an_unbounded_queue(self):
        entered, release = threading.Event(), threading.Event()

        class BlockingPredictor(Predictor):
            def predict(self, text):
                entered.set()
                if not release.wait(5):
                    raise RuntimeError('Test prediction timed out')
                return super().predict(text)

        app = create_app(self.config, predictor=BlockingPredictor())
        results = []
        worker = threading.Thread(target=lambda: results.append(app.test_client().post('/api/predict', json={'text': 'Opini IKN'})))
        worker.start()
        try:
            self.assertTrue(entered.wait(3))
            response = app.test_client().post('/api/predict', json={'text': 'Opini IKN lain'})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.get_json()['code'], 'model_busy')
            self.assertIn('Retry-After', response.headers)
        finally:
            release.set()
            worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(results[0].status_code, 200)

    def test_model_errors_do_not_disclose_internal_details(self):
        class BrokenPredictor(Predictor):
            def predict(self, text):
                raise ModelUnavailable('/private/checkpoint/config.json: secret diagnostic')

        app = create_app(self.config, predictor=BrokenPredictor())
        with self.assertLogs(app.logger, level='WARNING'):
            response = app.test_client().post('/api/predict', json={'text': 'Opini IKN'})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('/private', response.get_data(as_text=True))
        self.assertNotIn('secret diagnostic', response.get_data(as_text=True))

    def test_csv_export_quotes_cells_and_neutralizes_formula_prefixes(self):
        texts = ['=HYPERLINK("https://other.example")', ' \t+1', '\ttext', '\rtext', '\ufeff＝1+1', '@SUM(1,2)', 'teks, "IKN"']
        self.app.extensions['dataset'].rows = [dict(text=text, label='neutral', split='test', id=str(index)) for index, text in enumerate(texts)]
        response = self.client.get('/api/dataset/export')
        rows = list(csv.DictReader(io.StringIO(response.data.decode('utf-8-sig'))))
        self.assertEqual([row['text'] for row in rows[:-1]], ["'" + text for text in texts[:-1]])
        self.assertEqual(rows[-1]['text'], texts[-1])
        self.assertIn('attachment', response.headers['Content-Disposition'])
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')

    def test_corrupt_evaluation_reports_are_not_published(self):
        class EvaluatedPredictor(Predictor):
            def fingerprint(self):
                return 'expected-checkpoint'

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'reports').mkdir()
            app = create_app(self.config, predictor=EvaluatedPredictor())
            report = json.loads(json.dumps(calculate_metrics(['neutral'], ['neutral'])))
            report['model_fingerprint'] = 'expected-checkpoint'
            path = root / 'reports/test.json'
            with patch('server.APP_DIR', root):
                path.write_text(json.dumps(report))
                self.assertTrue(app.test_client().get('/api/evaluation').get_json()['available'])
                for invalid in [{**report, 'accuracy': float('nan')}, {**report, 'per_class': []}, {**report, 'confusion': [[1]]}]:
                    path.write_text(json.dumps(invalid))
                    response = app.test_client().get('/api/evaluation')
                    self.assertEqual(response.status_code, 200)
                    self.assertFalse(response.get_json()['available'])


class ModelSecurityTests(unittest.TestCase):
    def test_model_loading_requires_local_safetensors_and_disables_remote_code(self):
        manifest = dict(task='sentiment-classification', base_model='test', id2label={'0': 'positive', '1': 'neutral', '2': 'negative'}, preprocessing='raw', max_length=128, tokenization='indonlu-prefix')
        transformers = types.ModuleType('transformers')
        transformers.AutoConfig = Mock()
        transformers.AutoConfig.from_pretrained.return_value = types.SimpleNamespace(model_type='bert', num_labels=3, id2label=manifest['id2label'])
        transformers.BertTokenizer = Mock()
        transformers.BertForSequenceClassification = Mock()
        transformers.BertForSequenceClassification.from_pretrained.return_value = (Mock(), {})
        with tempfile.TemporaryDirectory() as temporary, patch.dict(sys.modules, {'torch': types.ModuleType('torch'), 'transformers': transformers}):
            root = Path(temporary)
            (root / 'serving.json').write_text(json.dumps(manifest))
            IndoBertService(root)._load()
        options = transformers.BertForSequenceClassification.from_pretrained.call_args.kwargs
        self.assertTrue(options['use_safetensors'])
        self.assertTrue(options['local_files_only'])
        self.assertFalse(options['trust_remote_code'])

    def test_request_budget_expires_without_growing_unbounded(self):
        budget = RequestBudget(limit=1, window=60)
        with patch('server.security.time.monotonic', side_effect=[0, 1, 61]):
            self.assertEqual(budget.retry_after(), 0)
            self.assertEqual(budget.retry_after(), 59)
            self.assertEqual(budget.retry_after(), 0)
        self.assertEqual(len(budget._requests), 1)

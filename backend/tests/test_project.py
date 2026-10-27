import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from server import create_app
from server.data import DatasetRepository
from server.inference import IndoBertService, ModelUnavailable, read_manifest
from server.preprocessing import Preprocessor, cleaning_text
from scripts.evaluate import calculate_metrics
from server.settings import DATA_DIR, NOTEBOOK, NOTEBOOKS_DIR, data_file
from server.tokenization import encode_batch
from notebook_export import export_checkpoint
from server.topics import get_topics
from scripts.train_topics import load_documents


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = DatasetRepository(DATA_DIR)

    def test_original_counts(self):
        result = self.data.summary()
        self.assertEqual(result['total'], 12520)
        self.assertEqual(result['counts'], dict(negative=8734, neutral=1846, positive=1940))
        self.assertEqual([result['splits'][name]['count'] for name in ('train', 'val', 'test')], [7512, 2504, 2504])

    def test_filters_and_ids(self):
        rows = self.data.filter(query='IKN', split='test', label='neutral')
        self.assertTrue(rows)
        self.assertTrue(all(row['split'] == 'test' and row['label'] == 'neutral' and 'ikn' in row['text'].lower() for row in rows))
        self.assertEqual(len({row['id'] for row in self.data.rows}), 12520)
        self.assertEqual(self.data.filter(query='unfindable-test-text-1234567890'), [])

    def test_saved_topic_outputs(self):
        result = self.data.topics()
        self.assertTrue(result['available'])
        self.assertEqual(result['groups']['negative']['coherence'], .5136)
        self.assertEqual(len(result['groups']['positive']['topics']), 2)
        self.assertEqual(result['groups']['positive']['topics'][0]['words'][0], 'indonesia')

    def test_training_reads_the_exact_notebook_tsvs(self):
        self.assertEqual([len(self.data.preprocessed(split)) for split in ('train', 'val', 'test')], [7498, 2502, 2501])
        self.assertEqual(self.data.preprocessed('test')[0]['label'], 'negative')

    def test_saved_prediction_metrics_have_correct_class_names(self):
        report = self.data.notebook_evaluation()
        self.assertEqual(report['count'], 2501)
        self.assertAlmostEqual(report['accuracy'], 1941 / 2501)
        self.assertEqual(report['labels'], ('positive', 'neutral', 'negative'))
        self.assertEqual(report['confusion'], [[233, 26, 129], [30, 125, 211], [71, 93, 1583]])
        self.assertEqual([row['support'] for row in report['per_class']], [388, 366, 1747])


class DataLayoutTests(unittest.TestCase):
    def test_grouped_files_take_precedence_over_legacy_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'raw').mkdir()
            (root / 'raw/example.csv').write_text('grouped')
            (root / 'example.csv').write_text('legacy')
            self.assertEqual(data_file(root, 'raw', 'example.csv').read_text(), 'grouped')

    def test_legacy_flat_directories_are_still_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for split in ('train', 'val', 'test'):
                (root / f'final_ikn_{split}_602020.csv').write_text('text,label\nIKN,neutral\n')
            rows = DatasetRepository(root).rows
            self.assertEqual(len(rows), 3)
            self.assertEqual({row['split'] for row in rows}, {'train', 'val', 'test'})

    def test_notebooks_can_be_configured_independently_of_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'Topic_Modelling_of_IKN.ipynb').write_text(json.dumps({'cells': []}))
            result = DatasetRepository(DATA_DIR, root).topics()
            self.assertFalse(result['available'])
            self.assertEqual(result['source'], 'Topic_Modelling_of_IKN.ipynb')

    def test_missing_sentiment_categories_have_explicit_zero_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for split in ('train', 'val', 'test'):
                (root / f'final_ikn_{split}_602020.csv').write_text('text,label\nIKN,neutral\n')
                (root / NOTEBOOK['datasets'][split]).write_text('IKN\tneutral\n')
            result = DatasetRepository(root).summary()
            self.assertEqual(result['splits']['test']['counts'], {'negative': 0, 'neutral': 1, 'positive': 0})


class TopicModellingTests(unittest.TestCase):
    def test_notebook_topic_api_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = get_topics(DatasetRepository(DATA_DIR), Path(temporary), 'notebook')
            self.assertTrue(result['available'])
            self.assertEqual(result['origin'], 'notebook')
            self.assertEqual(result['groups']['neutral']['coherence'], .3420)
            self.assertEqual(len(result['groups']['negative']['topics']), 2)

    def test_training_groups_documents_by_predictions(self):
        groups = load_documents(DATA_DIR / 'predictions/test_with_predictions new.csv')
        self.assertEqual(set(groups), {'positive', 'neutral', 'negative'})
        self.assertEqual(sum(map(len, groups.values())), 2501)
        self.assertEqual(len(groups['negative']), 1923)

    def test_missing_or_invalid_trained_results_have_clear_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = DatasetRepository(DATA_DIR)
            self.assertFalse(get_topics(repository, root, 'trained')['available'])
            (root / 'topics.json').write_text('{"algorithm":"SomethingElse","groups":{}}')
            self.assertFalse(get_topics(repository, root, 'trained')['available'])
            with self.assertRaises(ValueError):
                get_topics(repository, root, 'other')

    def test_trained_report_is_served_as_a_separate_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            groups = {label: dict(topics=[dict(number=0, words=['ikn', 'kota'])], coherence=.5, documents=25)
                      for label in ['positive', 'neutral', 'negative']}
            (root / 'topics.json').write_text(json.dumps(dict(algorithm='Top2Vec', source_file='test_with_predictions.csv', groups=groups)))
            result = get_topics(DatasetRepository(DATA_DIR), root, 'trained')
            self.assertTrue(result['available'])
            self.assertEqual(result['origin'], 'trained')
            self.assertEqual(result['source'], 'test_with_predictions.csv')


class PreprocessingTests(unittest.TestCase):
    def test_cleaning_matches_original_notebook(self):
        notebook = json.loads((NOTEBOOKS_DIR / 'Preprocessing_Datasets_IKN.ipynb').read_text())
        import ast
        import re
        source = '\n'.join(''.join(cell.get('source', [])) for cell in notebook['cells'] if cell['cell_type'] == 'code')
        # Extract and execute only the pure cleaning_text function, never notebook shell commands.
        start = source.index('def cleaning_text(')
        end = source.index('\n# Melakukan pembersihan data', start)
        namespace = {'re': re}
        exec(compile(ast.parse(source[start:end]), '<original-notebook-cleaning>', 'exec'), namespace)
        for text in ['HALOOO IKN 😊 #Nusantara @akun https://example.com/x?q=1',
                     'Tidak setuju! Proyek IKN 2025…', '\n  kota\nbaru, test!!! ', 'IKN di Kalimantan Timur.']:
            self.assertEqual(cleaning_text(text), namespace['cleaning_text'](text))

    def test_raw_preprocessing_is_explicit(self):
        self.assertEqual(Preprocessor('raw', APP.parent)('  Saya tidak mendukung IKN.  '), 'Saya tidak mendukung IKN.')
        with self.assertRaises(ValueError):
            Preprocessor('guess', APP.parent)


class EvaluationTests(unittest.TestCase):
    def test_metrics_are_calculated_from_actual_predictions(self):
        report = calculate_metrics(['negative', 'neutral', 'positive', 'positive'],
                                   ['negative', 'negative', 'positive', 'neutral'])
        self.assertEqual(report['confusion'], [[1, 1, 0], [0, 0, 1], [0, 0, 1]])
        self.assertEqual(report['accuracy'], .5)
        self.assertAlmostEqual(report['macro_f1'], 4 / 9)
        self.assertEqual(sum(row['support'] for row in report['per_class']), 4)

    def test_empty_or_misaligned_evaluation_is_rejected(self):
        for actual, predictions in [([], []), (['positive'], [])]:
            with self.assertRaises(ValueError):
                calculate_metrics(actual, predictions)


class CheckpointTests(unittest.TestCase):
    def manifest(self):
        # Test mapping deliberately differs from the previous browser model.
        return dict(task='sentiment-classification', base_model='test-only-indobert',
                    id2label={'0': 'positive', '1': 'neutral', '2': 'negative'},
                    preprocessing='raw', max_length=128, tokenization='indonlu-prefix')

    def test_missing_model_does_not_predict_with_a_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            model = IndoBertService(Path(temporary))
            self.assertEqual(model.status()['state'], 'missing_checkpoint')
            with self.assertRaises(ModelUnavailable):
                model.predict('Saya mendukung pembangunan IKN.')

    def test_label_order_is_read_from_notebook_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / 'serving.json').write_text(json.dumps(self.manifest()))
            _, labels = read_manifest(path)
            self.assertEqual(labels, {0: 'positive', 1: 'neutral', 2: 'negative'})
            self.assertEqual(IndoBertService(path).status()['state'], 'configured')

    def test_generic_labels_and_missing_pipeline_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            for change in [{'id2label': {'0': 'LABEL_0', '1': 'LABEL_1', '2': 'LABEL_2'}}, {'max_length': 0}, {'preprocessing': 'guess'}]:
                manifest = self.manifest() | change
                (path / 'serving.json').write_text(json.dumps(manifest))
                with self.assertRaises(ModelUnavailable):
                    read_manifest(path)


class NotebookAlignmentTests(unittest.TestCase):
    def test_notebook_export_has_confirmed_model_settings(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        model = SimpleNamespace(config=SimpleNamespace(model_type='bert', num_labels=3), save_pretrained=Mock())
        tokenizer = SimpleNamespace(save_pretrained=Mock())
        with tempfile.TemporaryDirectory() as temporary:
            export_checkpoint(model, tokenizer, temporary)
            manifest, labels = read_manifest(Path(temporary))
            self.assertEqual(labels, {0: 'positive', 1: 'neutral', 2: 'negative'})
            self.assertEqual(manifest['base_model'], 'indobenchmark/indobert-base-p1')
            self.assertEqual(manifest['preprocessing'], 'notebook')
            self.assertEqual(manifest['max_length'], 512)
            model.save_pretrained.assert_called_once_with(Path(temporary), safe_serialization=True)
            with self.assertRaises(ValueError):
                export_checkpoint(model, tokenizer, temporary, id2label={})

    def test_settings_match_the_actual_notebook(self):
        notebook = json.loads((NOTEBOOKS_DIR / NOTEBOOK['source']).read_text())
        self.assertIn(NOTEBOOK['base_model'], ''.join(notebook['cells'][9]['source']))
        mapping = ''.join(
            ''.join(output.get('text', [])) for output in notebook['cells'][16].get('outputs', []))
        self.assertIn("'positive': 0", mapping)
        self.assertIn("'negative': 2", mapping)
        self.assertIn('max_seq_len=512', ''.join(notebook['cells'][15]['source']))
        self.assertIn('lr=3e-6', ''.join(notebook['cells'][18]['source']))
        self.assertIn('n_epochs = 5', ''.join(notebook['cells'][19]['source']))

    def test_indonlu_tokenization_preserves_original_prefix_truncation(self):
        class Tokenizer:
            pad_token_id = 0
            def encode(self, text, add_special_tokens, truncation):
                self.assertions = (add_special_tokens, truncation)
                return [2, *range(10, 10 + int(text)), 3]
        tokenizer = Tokenizer()
        batch = encode_batch(tokenizer, ['1', '5'], max_length=5)
        self.assertEqual(batch['input_ids'], [[2, 10, 3, 0, 0], [2, 10, 11, 12, 13]])
        self.assertEqual(batch['attention_mask'], [[1., 1., 1., 0., 0.], [1., 1., 1., 1., 1.]])
        self.assertEqual(tokenizer.assertions, (True, False))


@unittest.skipUnless(importlib.util.find_spec('flask'), 'Flask belum terpasang di lingkungan ini')
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        app = create_app({'TESTING': True, 'MODEL_DIR': self.temporary.name,
                          'TOPIC_MODEL_DIR': self.temporary.name, 'TOPIC_REPORT_DIR': self.temporary.name})
        self.client = app.test_client()

    def test_api_root_and_summary(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/').get_json()['frontend'], 'http://localhost:3000')
        self.assertEqual(self.client.get('/api/summary').get_json()['total'], 12520)

    def test_topic_sources_and_validation(self):
        self.assertEqual(self.client.get('/api/topics?source=notebook').get_json()['groups']['positive']['coherence'], .3180)
        self.assertFalse(self.client.get('/api/topics?source=trained').get_json()['available'])
        self.assertEqual(self.client.get('/api/topics?source=other').status_code, 400)

    def test_model_missing_returns_503(self):
        result = self.client.post('/api/predict', json={'text': 'Saya mendukung pembangunan IKN.'})
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.get_json()['code'], 'model_unavailable')

    def test_input_validation(self):
        for payload in [[], {}, {'text': 1}, {'text': '   '}, {'text': '1234'}, {'text': 'a' * 2001}]:
            self.assertEqual(self.client.post('/api/predict', json=payload).status_code, 400)
        self.assertEqual(self.client.post('/api/predict', data='x').status_code, 415)
        self.assertEqual(self.client.post('/api/predict', data='{', content_type='application/json').status_code, 400)

    def test_filters_pagination_and_export(self):
        result = self.client.get('/api/dataset?split=test&label=positive&page_size=3').get_json()
        self.assertEqual(result['total'], 388)
        self.assertEqual(len(result['rows']), 3)
        self.assertEqual(self.client.get('/api/dataset?page=0').status_code, 400)
        self.assertEqual(self.client.get('/api/dataset?split=guess').status_code, 400)
        self.assertEqual(self.client.get('/api/dataset?page_size=999').status_code, 400)
        response = self.client.get('/api/dataset/export?split=test&label=positive')
        import csv, io
        self.assertEqual(len(list(csv.DictReader(io.StringIO(response.data.decode('utf-8-sig'))))), 388)

    def test_unavailable_evaluation_and_json_errors(self):
        self.assertFalse(self.client.get('/api/evaluation').get_json()['available'])
        self.assertEqual(self.client.get('/api/evaluation?source=notebook').get_json()['count'], 2501)
        self.assertEqual(self.client.get('/api/evaluation?source=unknown').status_code, 400)
        self.assertEqual(self.client.get('/api/predict').status_code, 405)
        self.assertIsInstance(self.client.get('/api/missing').get_json(), dict)


if __name__ == '__main__':
    unittest.main()

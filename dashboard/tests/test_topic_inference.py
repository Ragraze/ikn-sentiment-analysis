import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from server import create_app
from server.topics import LABELS, Top2VecService
from scripts.train_topics import load_documents


class TopicInferenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for label in LABELS:
            (self.root / f'model_top2vec_{label}').write_text('test fixture')
        self.model = Mock(embedding_model='doc2vec', vocab=['anggaran', 'bangun', 'ikn'])
        self.model.get_num_topics.return_value = 2
        # Topic IDs and document counts have different orders, as in Top2Vec's API.
        self.model.query_topics.return_value = (
            [['anggaran', 'bangun'], ['ikn', 'kota']], [[.81, .63], [.72, .6]], [.76, .22], [7, 2])
        self.model.get_topic_sizes.return_value = ([90, 35], [2, 7])
        self.top2vec = types.ModuleType('top2vec')
        self.top2vec.Top2Vec = Mock()
        self.top2vec.Top2Vec.load.return_value = self.model
        utils = types.ModuleType('gensim.utils')
        utils.simple_preprocess = lambda text: text.lower().split()
        self.modules = patch.dict(sys.modules, {'top2vec': self.top2vec, 'gensim': types.ModuleType('gensim'), 'gensim.utils': utils})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.service = Top2VecService(self.root)

    def test_sentence_uses_the_sentiment_specific_model_and_preserves_topic_ids(self):
        result = self.service.predict('anggaran bangun ikn', 'negative')
        self.assertTrue(result['available'])
        self.assertTrue(result['matched'])
        self.assertEqual(result['sentiment'], 'negative')
        self.assertEqual(result['topics'][0], dict(number=7, words=['anggaran', 'bangun'],
                                                 word_scores=[.81, .63], similarity=.76, documents=35))
        self.top2vec.Top2Vec.load.assert_called_once_with(str(self.root / 'model_top2vec_negative'))
        self.model.query_topics.assert_called_once_with(query='anggaran bangun ikn', num_topics=2)

    def test_models_are_loaded_once_per_sentiment_and_never_trained_on_requests(self):
        for label in ['positive', 'positive', 'neutral']:
            self.assertTrue(self.service.predict('bangun ikn', label)['matched'])
        self.assertEqual(self.top2vec.Top2Vec.load.call_count, 2)
        self.top2vec.Top2Vec.assert_not_called()

    def test_unknown_words_do_not_generate_a_random_doc2vec_topic(self):
        result = self.service.predict('xyzqv unrelated', 'positive')
        self.assertEqual(result['state'], 'no_match')
        self.assertFalse(result['matched'])
        self.assertEqual(result['topics'], [])
        self.model.query_topics.assert_not_called()

    def test_nonpositive_and_nonfinite_matches_are_not_shown_as_results(self):
        for score, expected in [(0, 'no_match'), (-.3, 'no_match'), (float('nan'), 'error'), (float('inf'), 'error'), (1.5, 'error')]:
            self.model.query_topics.return_value = ([['ikn']], [[.5]], [score], [2])
            if expected == 'error':
                with self.assertLogs('server.topics', level='ERROR'):
                    result = self.service.predict('ikn', 'positive')
            else:
                result = self.service.predict('ikn', 'positive')
            self.assertEqual(result['state'], expected)
            self.assertEqual(result['topics'], [])

    def test_corrupt_model_does_not_disclose_internal_details(self):
        self.top2vec.Top2Vec.load.side_effect = RuntimeError('/private/path secret')
        with self.assertLogs('server.topics', level='ERROR'):
            result = self.service.predict('ikn', 'neutral')
        self.assertFalse(result['available'])
        self.assertNotIn('secret', json.dumps(result))
        self.assertNotIn('/private', json.dumps(result))

    def test_failed_queries_update_health_and_a_successful_retry_recovers(self):
        self.model.query_topics.side_effect = RuntimeError('failed query')
        with self.assertLogs('server.topics', level='ERROR'):
            self.assertFalse(self.service.predict('ikn', 'positive')['available'])
        with patch('server.topics.importlib.util.find_spec', return_value=True):
            self.assertEqual(self.service.status()['groups']['positive']['state'], 'error')
            self.model.query_topics.side_effect = None
            self.assertTrue(self.service.predict('ikn', 'positive')['matched'])
            self.assertEqual(self.service.status()['groups']['positive']['state'], 'ready')

    def test_missing_model_does_not_import_or_train_top2vec(self):
        (self.root / 'model_top2vec_negative').unlink()
        result = self.service.predict('bangun ikn', 'negative')
        self.assertEqual(result['state'], 'missing_checkpoint')
        self.assertFalse(result['available'])
        self.top2vec.Top2Vec.load.assert_not_called()

    def test_only_local_doc2vec_models_are_accepted(self):
        self.model.embedding_model = 'universal-sentence-encoder'
        with self.assertLogs('server.topics', level='ERROR'):
            result = self.service.predict('ikn', 'positive')
        self.assertFalse(result['available'])
        self.model.query_topics.assert_not_called()

    def test_invalid_labels_and_limits_are_rejected_before_loading(self):
        with self.assertRaises(ValueError):
            self.service.predict('ikn', '../../model')
        for limit in [0, 11, True, 1.5]:
            with self.assertRaises(ValueError):
                self.service.predict('ikn', 'positive', limit)
        self.top2vec.Top2Vec.load.assert_not_called()

    def test_health_does_not_load_models_and_reports_dependency_availability(self):
        with patch('server.topics.importlib.util.find_spec', return_value=None):
            result = self.service.status()
        self.assertFalse(result['available'])
        self.assertTrue(all(group['state'] == 'missing_dependency' for group in result['groups'].values()))
        self.top2vec.Top2Vec.load.assert_not_called()

    def test_small_corpus_is_rejected_with_a_useful_message(self):
        source = self.root / 'predictions.csv'
        source.write_text('text,sentiment_predict\nIKN,positive\nIKN,neutral\nIKN,negative\n')
        with self.assertRaisesRegex(ValueError, 'minimal 20'):
            load_documents(source)


class CombinedAnalysisApiTests(unittest.TestCase):
    def predictor(self):
        predictor = Mock()
        predictor.predict.return_value = dict(label='negative', normalized='anggaran bangun ikn',
                                             scores={'positive': .1, 'neutral': .1, 'negative': .8}, confidence=.8)
        predictor.status.return_value = dict(state='ready', ready=True, model='IndoBERT')
        return predictor

    def test_api_returns_sentiment_and_topic_using_the_normalized_sentence(self):
        topics = Mock()
        topics.predict.return_value = dict(available=True, matched=True, topics=[dict(number=3, words=['anggaran'], similarity=.7)])
        topics.status.return_value = dict(available=True, model='Top2Vec')
        client = create_app({'TESTING': True}, predictor=self.predictor(), topic_predictor=topics).test_client()
        response = client.post('/api/predict', json={'text': 'Anggaran pembangunan IKN.'})
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result['label'], 'negative')
        self.assertEqual(result['topic_analysis']['topics'][0]['number'], 3)
        topics.predict.assert_called_once_with('anggaran bangun ikn', 'negative')
        self.assertTrue(client.get('/api/health').get_json()['topics']['available'])

    def test_sentiment_still_succeeds_when_topic_models_are_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = create_app({'TESTING': True, 'TOPIC_MODEL_DIR': temporary}, predictor=self.predictor()).test_client()
            result = client.post('/api/predict', json={'text': 'Anggaran pembangunan IKN.'})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.get_json()['confidence'], .8)
            self.assertEqual(result.get_json()['topic_analysis']['state'], 'missing_checkpoint')
            self.assertFalse(client.get('/api/health').get_json()['topics']['available'])

    def test_custom_topic_report_directory_is_used(self):
        with tempfile.TemporaryDirectory() as temporary:
            groups = {label: dict(topics=[dict(number=0, words=['ikn'])], coherence=.5) for label in LABELS}
            Path(temporary, 'topics.json').write_text(json.dumps(dict(algorithm='Top2Vec', source_file='local.csv', groups=groups)))
            client = create_app({'TESTING': True, 'TOPIC_REPORT_DIR': temporary}, predictor=self.predictor()).test_client()
            self.assertEqual(client.get('/api/topics?source=trained').get_json()['source'], 'local.csv')

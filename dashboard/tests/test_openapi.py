from html.parser import HTMLParser
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import create_app


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        url = values.get('src') if tag == 'script' else values.get('href') if tag == 'link' else None
        if url:
            self.urls.append(url)


class OpenApiTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.predictor = Mock()
        self.app = create_app({'TESTING': True, 'MODEL_DIR': temporary.name,
                               'TOPIC_MODEL_DIR': temporary.name, 'TOPIC_REPORT_DIR': temporary.name},
                              predictor=self.predictor)
        self.client = self.app.test_client()
        self.spec = self.client.get('/api/openapi.json').get_json()

    def test_spec_covers_api_routes_and_resolves_internal_references(self):
        response = self.client.get('/api/openapi.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        documented = {(path, method.upper()) for path, operations in self.spec['paths'].items()
                      for method in operations}
        actual = {(rule.rule, method) for rule in self.app.url_map.iter_rules()
                  if rule.rule.startswith('/api/') and not rule.rule.startswith('/api/docs')
                  and rule.rule != '/api/openapi.json' for method in rule.methods - {'HEAD', 'OPTIONS'}}
        self.assertEqual(documented, actual)
        identifiers = [operation['operationId'] for operations in self.spec['paths'].values()
                       for operation in operations.values()]
        self.assertEqual(len(identifiers), len(set(identifiers)))

        def check(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    self.assertTrue(value['$ref'].startswith('#/'))
                    target = self.spec
                    for part in value['$ref'][2:].split('/'):
                        target = target[part]
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)

        check(self.spec)
        self.predictor.status.assert_not_called()
        self.predictor.predict.assert_not_called()

    def test_swagger_serves_both_url_forms_and_all_assets_locally(self):
        for url in ['/api/docs', '/api/docs/']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'text/html')
                html = response.get_data(as_text=True)
                self.assertIn('/api/openapi.json', html)
                self.assertIn('"validatorUrl": null', html)
                parser = AssetParser()
                parser.feed(html)
                self.assertTrue(parser.urls)
                for asset in parser.urls:
                    self.assertTrue(asset.startswith('/api/docs/'), asset)
                    with self.client.get(asset) as asset_response:
                        self.assertEqual(asset_response.status_code, 200, asset)
        self.predictor.status.assert_not_called()
        self.predictor.predict.assert_not_called()

    def test_documented_dataset_limits_match_api_validation(self):
        params = self.spec['components']['parameters']
        for parameter, field in [('PageSize', 'page_size'), ('Page', 'page')]:
            maximum = params[parameter]['schema']['maximum']
            with self.subTest(field=field):
                self.assertEqual(self.client.get(f'/api/dataset?{field}={maximum}').status_code, 200)
                response = self.client.get(f'/api/dataset?{field}={maximum + 1}')
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.get_json())
        maximum = params['Query']['schema']['maxLength']
        self.assertEqual(self.client.get('/api/dataset', query_string={'q': 'x' * maximum}).status_code, 200)
        self.assertEqual(self.client.get('/api/dataset', query_string={'q': 'x' * (maximum + 1)}).status_code, 400)

    def test_swagger_post_uses_existing_same_origin_validation(self):
        self.predictor.predict.return_value = {
            'label': 'neutral', 'confidence': 1.0,
            'scores': {'positive': 0, 'neutral': 1, 'negative': 0},
            'normalized': 'opini ikn', 'model': 'IndoBERT', 'base_model': 'test',
        }
        response = self.client.post('/api/predict', json={'text': 'Opini IKN'},
                                    headers={'Origin': 'http://localhost', 'Sec-Fetch-Site': 'same-origin'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['label'], 'neutral')
        self.assertFalse(response.get_json()['topic_analysis']['available'])
        self.predictor.predict.assert_called_once_with('Opini IKN')
        response = self.client.post('/api/predict', json={'text': 'Opini IKN'},
                                    headers={'Origin': 'https://other.example', 'Sec-Fetch-Site': 'cross-site'})
        self.assertEqual(response.status_code, 403)
        self.predictor.predict.assert_called_once()

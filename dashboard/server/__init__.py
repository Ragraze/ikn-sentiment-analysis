"""Flask application and same-origin IndoBERT API."""
import csv
import io
import os
from pathlib import Path
import threading

from .data import DatasetRepository
from .inference import IndoBertService, ModelUnavailable
from .metrics import validate_metrics
from .settings import APP_DIR, PROJECT_DIR
from .security import RequestBudget, origin_of, spreadsheet_text
from .topics import Top2VecService, get_topics


def create_app(config=None, predictor=None, topic_predictor=None):
    from flask import Flask, Response, jsonify, request
    from werkzeug.exceptions import HTTPException

    app = Flask(__name__, static_folder=None)
    app.config.update(MAX_CONTENT_LENGTH=16_384,
                      DATA_DIR=os.environ.get('IKN_DATA_DIR', str(PROJECT_DIR / 'data')),
                      NOTEBOOKS_DIR=os.environ.get('IKN_NOTEBOOKS_DIR', str(PROJECT_DIR / 'notebooks')),
                      MODEL_DIR=os.environ.get('INDOBERT_MODEL_DIR', str(APP_DIR / 'models' / 'indobert-ikn')),
                      MODEL_DEVICE=os.environ.get('INDOBERT_DEVICE', 'cpu'),
                      TOPIC_MODEL_DIR=os.environ.get('TOP2VEC_MODEL_DIR', str(APP_DIR / 'models' / 'top2vec')),
                      TOPIC_REPORT_DIR=os.environ.get('TOP2VEC_REPORT_DIR', str(APP_DIR / 'reports')),
                      TRUSTED_HOSTS=os.environ.get('IKN_TRUSTED_HOSTS', 'localhost,127.0.0.1,[::1]').split(','),
                      PREDICTION_LIMIT=30,
                      FRONTEND_URL=os.environ.get('FRONTEND_URL', 'http://localhost:3000'))
    if config:
        app.config.update(config)
    repository = DatasetRepository(Path(app.config['DATA_DIR']), Path(app.config['NOTEBOOKS_DIR']))
    service = predictor or IndoBertService(Path(app.config['MODEL_DIR']), app.config['MODEL_DEVICE'], Path(app.config['DATA_DIR']))
    topic_service = topic_predictor or Top2VecService(Path(app.config['TOPIC_MODEL_DIR']))
    app.extensions.update(dataset=repository, indobert=service, top2vec=topic_service)
    prediction_slot = threading.BoundedSemaphore(1)
    prediction_budget = RequestBudget(limit=app.config['PREDICTION_LIMIT'])
    frontend_origin = origin_of(app.config['FRONTEND_URL'])
    if frontend_origin is None:
        raise ValueError('FRONTEND_URL harus berupa URL HTTP atau HTTPS yang valid.')

    @app.before_request
    def validate_origin():
        if request.method == 'POST' and request.path.startswith('/api/'):
            origin = request.headers.get('Origin')
            if request.headers.get('Sec-Fetch-Site') == 'cross-site' or (
                origin and origin_of(origin) not in (frontend_origin, origin_of(request.host_url))
            ):
                return jsonify(error='Asal permintaan tidak diizinkan.'), 403

    @app.get('/')
    def index():
        return jsonify(service='IKN Sentiment Lab API', frontend=app.config['FRONTEND_URL'],
                       message='Buka frontend Next.js untuk menggunakan dashboard.')

    @app.get('/api/health')
    def health():
        return jsonify({**service.status(), 'topics': topic_service.status()})

    @app.get('/api/summary')
    def summary():
        return jsonify(repository.summary())

    @app.get('/api/topics')
    def topics():
        try:
            return jsonify(get_topics(repository, Path(app.config['TOPIC_REPORT_DIR']), request.args.get('source', 'notebook')))
        except ValueError as error:
            return jsonify(error=str(error)), 400

    def filters():
        split = request.args.get('split', 'all')
        label = request.args.get('label', 'all')
        if split not in ('all', 'train', 'val', 'test') or label not in ('all', 'negative', 'neutral', 'positive'):
            raise ValueError('Filter dataset atau sentimen tidak valid.')
        query = request.args.get('q', '').strip()
        if len(query) > 200:
            raise ValueError('Pencarian maksimal 200 karakter.')
        if any(len(request.args.getlist(key)) != 1 for key in request.args):
            raise ValueError('Parameter filter tidak boleh berulang.')
        return repository.filter(query, split, label)

    @app.get('/api/dataset')
    def dataset():
        try:
            rows = filters()
            page = int(request.args.get('page', '1'))
            size = int(request.args.get('page_size', '8'))
            if not 1 <= page <= 1_000_000 or not 1 <= size <= 50:
                raise ValueError('Halaman harus 1–1.000.000 dan page_size antara 1–50.')
        except ValueError as error:
            return jsonify(error=str(error)), 400
        start = (page - 1) * size
        return jsonify(rows=rows[start:start + size], total=len(rows), page=page, page_size=size)

    @app.get('/api/dataset/export')
    def export_data():
        try:
            rows = filters()
        except ValueError as error:
            return jsonify(error=str(error)), 400
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(['text', 'label', 'split'])
        for row in rows:
            writer.writerow([spreadsheet_text(row['text']), row['label'], row['split']])
        return Response(output.getvalue(), content_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition': 'attachment; filename="ikn-dataset.csv"'})

    @app.post('/api/predict')
    def predict():
        if not request.is_json:
            return jsonify(error='Gunakan Content-Type: application/json.'), 415
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get('text'), str):
            return jsonify(error='Body harus berupa objek JSON dengan field text bertipe string.'), 400
        text = payload['text'].strip()
        if not text or not any(char.isalpha() for char in text):
            return jsonify(error='Masukkan kalimat yang mengandung huruf.'), 400
        if len(text) > 2000:
            return jsonify(error='Kalimat maksimal 2.000 karakter.'), 400
        if any(0xD800 <= ord(char) <= 0xDFFF or (ord(char) < 32 and char not in '\t\r\n') for char in text):
            return jsonify(error='Kalimat mengandung karakter kontrol yang tidak didukung.'), 400
        delay = prediction_budget.retry_after()
        if delay:
            return jsonify(error='Batas analisis tercapai. Coba lagi sebentar.', code='rate_limited'), 429, {'Retry-After': str(delay)}
        if not prediction_slot.acquire(blocking=False):
            return jsonify(error='Model sedang memproses kalimat lain. Coba lagi sebentar.', code='model_busy'), 503, {'Retry-After': '3'}
        try:
            result = service.predict(text)
            result['topic_analysis'] = topic_service.predict(result.get('normalized', text), result['label'])
            return jsonify(result)
        except ModelUnavailable as error:
            app.logger.warning('Model unavailable: %s', error)
            return jsonify(error='Model belum dapat digunakan. Minta pengelola memeriksa checkpoint dan layanan analisis.', code='model_unavailable'), 503
        except ValueError as error:
            return jsonify(error=str(error)), 422
        except Exception:
            app.logger.exception('IndoBERT inference failed')
            return jsonify(error='Inferensi IndoBERT gagal. Periksa log backend.'), 500
        finally:
            prediction_slot.release()

    @app.get('/api/evaluation')
    def evaluation():
        if request.args.get('source', 'checkpoint') == 'notebook':
            return jsonify(repository.notebook_evaluation())
        if request.args.get('source', 'checkpoint') != 'checkpoint':
            return jsonify(error='Sumber evaluasi tidak dikenal.'), 400
        # Metrics must be tied to the exact checkpoint, never to another model.
        report_path = APP_DIR / 'reports' / 'test.json'
        if not report_path.is_file():
            return jsonify(available=False, message='Evaluasi checkpoint IndoBERT belum dijalankan.')
        try:
            import json
            report = json.loads(report_path.read_text())
            if not isinstance(report, dict) or report.get('model_fingerprint') != service.fingerprint():
                return jsonify(available=False, message='Checkpoint berubah. Jalankan ulang evaluasi IndoBERT.')
            validate_metrics(report)
            return jsonify({**report, 'available': True})
        except (ValueError, OSError, ModelUnavailable, TypeError):
            return jsonify(available=False, message='Evaluasi belum tersedia untuk checkpoint ini.')

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            message = 'Terjadi kesalahan pada layanan.' if error.code >= 500 else error.description
            return jsonify(error=message), error.code
        return error

    @app.errorhandler(FileNotFoundError)
    def missing_data(error):
        app.logger.error('Required project file missing: %s', error)
        return jsonify(error='File dataset belum tersedia. Periksa IKN_DATA_DIR dan file CSV proyek.'), 503

    @app.after_request
    def headers(response):
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    return app

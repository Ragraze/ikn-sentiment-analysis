def ref(name):
    return {'$ref': f'#/components/schemas/{name}'}


def obj(properties, required=()):
    schema = {'type': 'object', 'properties': properties}
    if required:
        schema['required'] = list(required)
    return schema


def array(items):
    return {'type': 'array', 'items': items}


def response(description, schema):
    return {'description': description, 'content': {'application/json': {'schema': schema}}}


def parameter(name):
    return {'$ref': f'#/components/parameters/{name}'}


def query(name, schema, description):
    return {'name': name, 'in': 'query', 'description': description, 'schema': schema}


STRING = {'type': 'string'}
BOOLEAN = {'type': 'boolean'}
COUNT = {'type': 'integer', 'minimum': 0}
SCORE = {'type': 'number', 'minimum': 0, 'maximum': 1}
LABELS = ('positive', 'neutral', 'negative')
ERROR = response('Permintaan gagal. Field code tersedia pada kegagalan prediksi tertentu.', ref('Error'))
UNAVAILABLE = response('Dataset atau model belum tersedia, atau layanan sedang sibuk.', ref('Error'))
UNAVAILABLE['headers'] = {
    'Retry-After': {'description': 'Waktu tunggu dalam detik ketika model sedang sibuk.',
                    'schema': {'type': 'integer', 'minimum': 1}},
}

SCHEMAS = {
    'Error': obj({'error': STRING, 'code': STRING}, ('error',)),
    'Sentiment': {'type': 'string', 'enum': list(LABELS)},
    'Split': {'type': 'string', 'enum': ['train', 'val', 'test']},
    'Counts': obj({label: COUNT for label in LABELS}, LABELS),
    'Scores': obj({label: SCORE for label in LABELS}, LABELS),
    'Topic': obj({
        'number': COUNT, 'words': array(STRING),
        'word_scores': array({'type': 'number'}), 'documents': COUNT,
    }, ('number', 'words')),
    'TopicGroup': obj({
        'topics': array(ref('Topic')), 'coherence': {'type': 'number', 'nullable': True},
        'documents': COUNT,
    }, ('topics', 'coherence')),
    'TopicGroups': obj({label: ref('TopicGroup') for label in LABELS}),
    'Topics': obj({
        'available': BOOLEAN, 'source': {'type': 'string', 'nullable': True},
        'origin': {'type': 'string', 'enum': ['notebook', 'trained']}, 'message': STRING,
        'groups': ref('TopicGroups'), 'trained_at': {'type': 'string', 'nullable': True},
        'parameters': {'type': 'object', 'nullable': True},
    }, ('available', 'source', 'groups')),
    'SplitSummary': obj({'count': COUNT, 'counts': ref('Counts')}, ('count', 'counts')),
    'Summary': obj({
        'total': COUNT, 'counts': ref('Counts'),
        'splits': obj({split: ref('SplitSummary') for split in ('train', 'val', 'test')}, ('train', 'val', 'test')),
        'preprocessed': obj({split: COUNT for split in ('train', 'val', 'test')}, ('train', 'val', 'test')),
        'notebook': {'type': 'object', 'description': 'Konfigurasi training dari notebook penelitian.'},
        'topics': ref('Topics'),
    }, ('total', 'counts', 'splits', 'preprocessed', 'notebook', 'topics')),
    'TopicModelStatus': obj({
        'available': BOOLEAN,
        'state': {'type': 'string', 'enum': ['missing_checkpoint', 'missing_dependency', 'configured', 'ready', 'error']},
    }, ('available', 'state')),
    'Health': obj({
        'ready': BOOLEAN,
        'state': {'type': 'string', 'enum': ['missing_checkpoint', 'configured', 'ready', 'error']},
        'model': STRING, 'base_model': STRING, 'preprocessing': STRING,
        'max_length': {'type': 'integer', 'minimum': 2, 'maximum': 512}, 'message': STRING,
        'topics': obj({
            'model': STRING, 'available': BOOLEAN,
            'groups': obj({label: ref('TopicModelStatus') for label in LABELS}, LABELS),
        }, ('model', 'available', 'groups')),
    }, ('ready', 'state', 'model', 'base_model', 'max_length', 'message', 'topics')),
    'DatasetRow': obj({
        'id': STRING, 'text': STRING, 'label': ref('Sentiment'), 'split': ref('Split'),
    }, ('id', 'text', 'label', 'split')),
    'DatasetPage': obj({
        'rows': array(ref('DatasetRow')), 'total': COUNT,
        'page': {'type': 'integer', 'minimum': 1, 'maximum': 1000000},
        'page_size': {'type': 'integer', 'minimum': 1, 'maximum': 50},
    }, ('rows', 'total', 'page', 'page_size')),
    'PredictionInput': obj({
        'text': {'type': 'string', 'minLength': 1, 'maxLength': 2000,
                 'description': 'Opini berbahasa Indonesia. Harus mengandung huruf dan tidak boleh kosong setelah trim atau preprocessing.',
                 'example': 'Saya mendukung pembangunan ibu kota Nusantara.'},
    }, ('text',)),
    'TopicMatch': obj({
        'number': COUNT, 'words': array(STRING), 'word_scores': array({'type': 'number'}),
        'documents': COUNT, 'similarity': {'type': 'number', 'minimum': -1, 'maximum': 1,
                                          'description': 'Kemiripan cosine, bukan persentase probabilitas.'},
    }, ('number', 'words', 'word_scores', 'documents', 'similarity')),
    'TopicAnalysis': obj({
        'model': STRING, 'sentiment': ref('Sentiment'), 'available': BOOLEAN, 'matched': BOOLEAN,
        'state': {'type': 'string', 'enum': ['ready', 'no_match', 'missing_checkpoint', 'error']},
        'message': STRING, 'topics': array(ref('TopicMatch')),
    }, ('model', 'sentiment', 'available', 'matched', 'state', 'message', 'topics')),
    'Prediction': obj({
        'label': ref('Sentiment'), 'confidence': SCORE, 'scores': ref('Scores'),
        'normalized': STRING, 'model': STRING, 'base_model': STRING,
        'topic_analysis': ref('TopicAnalysis'),
    }, ('label', 'confidence', 'scores', 'normalized', 'model', 'base_model', 'topic_analysis')),
    'ClassMetrics': obj({
        'label': ref('Sentiment'), 'precision': SCORE, 'recall': SCORE, 'f1': SCORE, 'support': COUNT,
    }, ('label', 'precision', 'recall', 'f1', 'support')),
    'Evaluation': obj({
        'available': BOOLEAN, 'message': STRING, 'source': STRING, 'source_file': STRING,
        'dataset': STRING, 'evaluated_at': {'type': 'string', 'format': 'date-time'},
        'count': COUNT, 'accuracy': SCORE, 'macro_f1': SCORE,
        'labels': array(ref('Sentiment')), 'confusion': array(array(COUNT)),
        'per_class': array(ref('ClassMetrics')), 'model_fingerprint': STRING,
    }, ('available',)),
}

FILTERS = [parameter(name) for name in ('Query', 'SplitFilter', 'SentimentFilter')]

SPEC = {
    'openapi': '3.0.3',
    'info': {
        'title': 'IKN Sentiment Lab API', 'version': '1.0.0',
        'description': 'API Flask untuk dataset opini IKN, klasifikasi sentimen IndoBERT, dan pemodelan topik Top2Vec. '
                       'Tidak memerlukan API key. Model dijalankan lokal; checkpoint dan dependensinya perlu tersedia. '
                       'Try it out menjalankan request sungguhan. Prediksi memuat model saat pertama dipakai, '
                       'dibatasi 30 permintaan valid per menit per proses, dan satu inferensi aktif per proses.',
    },
    'servers': [{'url': '/', 'description': 'Server yang menyajikan dokumentasi ini.'}],
    'tags': [
        {'name': 'Layanan', 'description': 'Informasi API dan kesiapan model.'},
        {'name': 'Dataset', 'description': 'Ringkasan, pencarian, dan ekspor opini penelitian.'},
        {'name': 'Analisis', 'description': 'Prediksi sentimen dan topik kalimat.'},
        {'name': 'Topik', 'description': 'Hasil pemodelan topik per sentimen.'},
        {'name': 'Evaluasi', 'description': 'Metrik klasifikasi dan confusion matrix.'},
    ],
    'paths': {
        '/api/health': {'get': {
            'operationId': 'getHealth', 'tags': ['Layanan'], 'summary': 'Periksa kesiapan IndoBERT dan Top2Vec',
            'description': 'Pemeriksaan ini tidak memuat model. State configured berarti checkpoint tersedia; '
                           'ready berarti model sudah dimuat. HTTP 200 tetap digunakan ketika model belum siap.',
            'responses': {'200': response('Status model dan dependensi.', ref('Health'))},
        }},
        '/api/summary': {'get': {
            'operationId': 'getSummary', 'tags': ['Dataset'], 'summary': 'Ringkasan dataset dan sentimen',
            'responses': {'200': response('Jumlah opini, pembagian data, dan topik notebook.', ref('Summary')),
                          '503': UNAVAILABLE},
        }},
        '/api/dataset': {'get': {
            'operationId': 'getDataset', 'tags': ['Dataset'], 'summary': 'Cari dan saring opini dengan pagination',
            'description': 'Pencarian tidak membedakan huruf besar/kecil. Parameter query tidak boleh berulang.',
            'parameters': FILTERS + [parameter('Page'), parameter('PageSize')],
            'responses': {'200': response('Satu halaman hasil dan total opini sesuai filter.', ref('DatasetPage')),
                          '400': ERROR, '503': UNAVAILABLE},
        }},
        '/api/dataset/export': {'get': {
            'operationId': 'exportDataset', 'tags': ['Dataset'], 'summary': 'Unduh opini sebagai CSV',
            'description': 'Mengekspor seluruh hasil filter tanpa pagination. CSV memakai UTF-8 dengan BOM '
                           'dan kolom text, label, split. Teks yang berisiko menjadi formula spreadsheet diberi awalan apostrof.',
            'parameters': FILTERS,
            'responses': {
                '200': {'description': 'File ikn-dataset.csv.',
                        'headers': {'Content-Disposition': {'schema': STRING, 'example': 'attachment; filename="ikn-dataset.csv"'}},
                        'content': {'text/csv': {'schema': {'type': 'string', 'format': 'binary'}}}},
                '400': ERROR, '503': UNAVAILABLE,
            },
        }},
        '/api/predict': {'post': {
            'operationId': 'predictSentiment', 'tags': ['Analisis'], 'summary': 'Analisis sentimen dan topik sebuah opini',
            'description': 'Kalimat diproses dengan preprocessing notebook, lalu IndoBERT dan Top2Vec sesuai sentimen. '
                           'Sentimen tetap dikembalikan jika model topik belum tersedia atau tidak menemukan kecocokan. '
                           'Request lintas origin yang tidak diizinkan ditolak. Batas body adalah 16.384 byte.',
            'requestBody': {'required': True, 'content': {'application/json': {'schema': ref('PredictionInput')}}},
            'responses': {
                '200': response('Sentimen, skor model, teks hasil preprocessing, dan topik terdekat.', ref('Prediction')),
                '400': ERROR, '403': response('Origin permintaan tidak diizinkan.', ref('Error')),
                '413': response('Body request melebihi 16.384 byte.', ref('Error')),
                '415': response('Gunakan Content-Type: application/json.', ref('Error')),
                '422': response('Kalimat tidak dapat diproses, misalnya kosong setelah preprocessing.', ref('Error')),
                '429': {'description': 'Batas prediksi tercapai.',
                        'headers': {'Retry-After': {'schema': {'type': 'integer', 'minimum': 1},
                                                    'description': 'Waktu tunggu dalam detik sebelum mencoba lagi.'}},
                        'content': {'application/json': {'schema': ref('Error')}}},
                '500': response('Inferensi IndoBERT gagal.', ref('Error')), '503': UNAVAILABLE,
            },
        }},
        '/api/topics': {'get': {
            'operationId': 'getTopics', 'tags': ['Topik'], 'summary': 'Daftar topik dan coherence per sentimen',
            'description': 'Sumber notebook membaca output penelitian yang tersimpan. Sumber trained membaca '
                           'laporan training proyek. HTTP 200 dengan available=false berarti laporan belum tersedia atau tidak valid.',
            'parameters': [parameter('TopicSource')],
            'responses': {'200': response('Kelompok topik, kata kunci, bobot jika tersedia, dan coherence.', ref('Topics')),
                          '400': ERROR, '503': UNAVAILABLE},
        }},
        '/api/evaluation': {'get': {
            'operationId': 'getEvaluation', 'tags': ['Evaluasi'], 'summary': 'Metrik klasifikasi dan confusion matrix',
            'description': 'Sumber checkpoint memeriksa fingerprint laporan terhadap checkpoint aktif. Sumber notebook '
                           'menghitung metrik dari CSV prediksi penelitian. HTTP 200 dengan available=false berarti '
                           'evaluasi belum tersedia. Urutan kelas adalah positive, neutral, negative; baris confusion '
                           'matrix adalah label aktual dan kolom adalah prediksi.',
            'parameters': [parameter('EvaluationSource')],
            'responses': {'200': response('Ketersediaan evaluasi dan metrik jika tersedia.', ref('Evaluation')),
                          '400': ERROR, '503': UNAVAILABLE},
        }},
    },
    'components': {
        'schemas': SCHEMAS,
        'parameters': {
            'Query': query('q', {'type': 'string', 'maxLength': 200, 'default': ''}, 'Kata atau potongan kalimat.'),
            'SplitFilter': query('split', {'type': 'string', 'enum': ['all', 'train', 'val', 'test'], 'default': 'all'}, 'Bagian dataset.'),
            'SentimentFilter': query('label', {'type': 'string', 'enum': ['all', *LABELS], 'default': 'all'}, 'Label sentimen asli.'),
            'Page': query('page', {'type': 'integer', 'minimum': 1, 'maximum': 1000000, 'default': 1}, 'Nomor halaman dimulai dari 1.'),
            'PageSize': query('page_size', {'type': 'integer', 'minimum': 1, 'maximum': 50, 'default': 8}, 'Jumlah opini per halaman.'),
            'TopicSource': query('source', {'type': 'string', 'enum': ['notebook', 'trained'], 'default': 'notebook'}, 'Sumber hasil pemodelan topik.'),
            'EvaluationSource': query('source', {'type': 'string', 'enum': ['checkpoint', 'notebook'], 'default': 'checkpoint'}, 'Sumber metrik evaluasi.'),
        },
    },
}

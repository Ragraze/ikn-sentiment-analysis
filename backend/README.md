# IKN Sentiment Lab: Next.js + Flask + IndoBERT + Top2Vec

A dashboard and Python API adapted from the three notebooks in `../notebooks/`:

1. `Preprocessing_Datasets_IKN.ipynb`: text cleaning, tokenization, removal of slang, stopwords, and English words, and Sastrawi stemming.
2. `Sentimen_Analysis_IKN_IndoBERT.ipynb`: IndoBERT fine-tuning and evaluation for three sentiment classes.
3. `Topic_Modelling_of_IKN.ipynb`: Top2Vec models for each sentiment and coherence scores.

The **Next.js App Router + React + TypeScript** frontend requests data and predictions from the **Flask** backend. Next.js forwards `/api/*` requests to Flask, allowing the browser to use a single origin without additional CORS configuration. Classification uses PyTorch/IndoBERT, and topic modelling uses Top2Vec.

This guide covers the research pipeline in detail. For an overview of features, architecture, API request examples, and troubleshooting, see the [main README](../README.md).

## Table of contents

- [Running the application](#running-the-application)
- [API documentation](#api-documentation)
- [Dashboard pages](#dashboard-pages)
- [Importing a Colab checkpoint ZIP](#importing-a-colab-checkpoint-zip)
- [Configuration from the notebook](#configuration-from-the-notebook)
- [Preprocessing and tokenization consistency](#preprocessing-and-tokenization-consistency)
- [Exporting from a trained notebook runtime](#exporting-from-a-trained-notebook-runtime)
- [Evaluation and notebook results](#evaluation-and-notebook-results)
- [Top2Vec topic modelling](#top2vec-topic-modelling)
- [Application structure](#application-structure)
- [Environment variables](#environment-variables)
- [Testing](#testing)
- [References](#references)

## Running the application

Use Python 3.11 or 3.12, Node.js >= 20.9, and an internet connection for dependency installation and the initial model/resource downloads.

**Model checkpoints are excluded from GitHub clones.** The checkpoint evaluation report `reports/test.json` is included; other generated reports and prediction CSVs are ignored by Git. Datasets and notebook outputs are also included, so exploration and historical evaluation are available before local models are installed. Sentence prediction requires an IndoBERT checkpoint, and sentence-to-topic matching requires Top2Vec models.

On Linux/WSL, if a checkpoint or notebook export is already installed at the default location, backend setup can be run with one command:

```bash
cd backend
bash scripts/setup_backend.sh
.venv/bin/python run.py
```

The script prepares a virtual environment, pip, CPU PyTorch, backend dependencies, and NLTK resources. It then runs tests and attempts a prediction using the local checkpoint through Flask's test client, without opening a network port. It stops if any step fails. If no checkpoint is installed, prediction verification fails; use the manual installation below, then import or train a model. Python 3.10 is also supported; select an interpreter with `IKN_SETUP_PYTHON=python3.12 bash scripts/setup_backend.sh`. Downloads require access to PyPI, `download.pytorch.org`, and the NLTK resource servers. The script can be rerun to resume an interrupted installation.

For manual installation, use the following steps.

Start the backend in the first terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/setup_nltk.py
python run.py
```

Start the frontend in the second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000** for the dashboard. The backend API runs at **http://127.0.0.1:5000**. On Windows, activate the virtual environment with `.venv\Scripts\activate` in Command Prompt, or `.\.venv\Scripts\Activate.ps1` in PowerShell.

## Docker

From the repository root, run:

```bash
docker compose up --build -d
```

Open http://localhost:3000. Compose runs the Next.js frontend and a CPU backend with Gunicorn and Top2Vec dependencies. Only the frontend port is published; API requests are forwarded internally to the backend. Dataset and notebook folders from the repository are mounted read-only. Local model files in `backend/models/` are copied into the backend image; install checkpoints before building for sentence prediction, and rebuild after replacing them. Missing checkpoints do not prevent dataset exploration.

For a different local port, set both `FRONTEND_PORT` and `FRONTEND_URL`, for example `FRONTEND_PORT=3002 FRONTEND_URL=http://localhost:3002 docker compose up -d`. The published port is bound to loopback. The first build downloads dependencies and NLTK resources. Stop the services with `docker compose down`.

## API documentation

Open **http://127.0.0.1:5000/api/docs/** for Swagger UI, or **http://localhost:3000/api/docs/** through the frontend. The OpenAPI specification is available at `/api/openapi.json`. For an existing installation, run `python -m pip install -r requirements.txt` and restart the backend to install any newly required packages.

Swagger documents model status, dataset summaries, search and CSV export, sentence prediction, topics, and evaluation. Expand an endpoint, select **Try it out**, enter parameters or JSON, and choose **Execute**. Requests use the same origin and require no API key. Swagger assets are served by the backend; predictions require a local checkpoint and follow the same request limits as the dashboard.

Endpoint lists, parameters, `curl` examples, and response codes are available in the [main README's API documentation](../README.md#api-documentation-and-usage). Complete schemas are defined in [server/openapi.py](server/openapi.py).

`/api/health` does not load models and can return HTTP 200 even when a checkpoint is unavailable. For IndoBERT, `configured` means a checkpoint manifest was detected, while `ready` means the model loaded successfully. Also inspect the per-sentiment status in `topics.groups`. Missing topic or evaluation reports are indicated by `available=false`.

## Dashboard pages

The sidebar provides navigation to five pages:

| Page | Address | Contents |
| --- | --- | --- |
| Dashboard | `/` | Dataset summary, sentiment proportion donut, grouped bars for dataset splits, topic counts, and model status |
| Sentence analysis | `/analysis` | Opinion input, sentiment prediction, and matching topics |
| Opinion dataset | `/dataset` | Search, filters, pagination, and CSV export |
| Topic modelling | `/topics` | Keywords, weights, and coherence; project training results are the default source |
| Model evaluation | `/evaluation` | Project checkpoint or notebook metrics, confusion matrix, per-class results, and report provenance |

Below 1280px, including tablet layouts, the hamburger **Menu** button opens the sidebar. Close it with the close button, Escape, or a click outside the panel. Selecting a page also closes the menu. The GitHub button stays in the lower-right corner and opens the project repository in a new tab. Dashboard charts use actual API data. The dataset split filter updates sentiment proportions, and the selected topic source is carried into the detail page. The comparison chart includes a table with exact values for each bar.

The interface uses Indonesian labels. On the analysis page, **Ctrl/Cmd + Enter** submits an analysis, **Salin hasil** (Copy results) copies the sentence and result summary, and **Urungkan** (Undo) restores a cleared sentence. The latest input and result remain available while navigating within the application and reset on page reload. **Batalkan** (Cancel) aborts the browser request and clears its pending result; computation already accepted by the backend may continue.

The dataset page offers filter reset and 8/16/32/50 opinions per page. Export and pagination wait for search/filter updates to finish so downloaded results match the active filters. The evaluation page explains the result source and includes an expandable **Cara membaca metrik evaluasi** (How to read evaluation metrics) section.

For the production frontend, run `npm run build` followed by `npm start`. To change the backend URL, copy `frontend/.env.example` to `frontend/.env.local` and set `FLASK_API_URL`. Restart Next.js after configuration changes and rebuild for production.

Training is needed only when preparing or replacing a model. For subsequent use, start the backend and frontend without retraining. Dataset summaries and historical notebook results remain available before a checkpoint is installed. The prediction panel reports the actual model status.

If no checkpoint is available, run the following from `backend/` after installation:

```bash
python scripts/setup_nltk.py
python scripts/train.py
python scripts/evaluate.py
```

If a trained Colab model is already available, use the export instructions below to reuse it.

Install an existing fine-tuned Colab checkpoint in **`models/indobert-ikn/`**, the backend's default location. That model can be used without retraining. ZIP archives and installed checkpoints are local files excluded from GitHub.

## Importing a Colab checkpoint ZIP

Provide your own fine-tuned checkpoint ZIP and an empty destination directory. For example, if the archive is stored at the following path:

```bash
python scripts/import_checkpoint.py models/indobert_model_3e6.zip
```

The script extracts the checkpoint, checks its safetensors structure and three-class classifier, and creates the serving configuration. Generic labels `LABEL_0`, `LABEL_1`, and `LABEL_2` in the ZIP are mapped using the notebook: **positive=0, neutral=1, negative=2**. The legacy `_num_labels` value is normalized using the classifier shape stored in the weights.

The ZIP stores the vocabulary in `tokenizer.json`. The script writes `vocab.txt` using the same indices for `BertTokenizer` compatibility. Model weights and the source archive are preserved. The original configuration is saved as `config.original.json`, and checksums and validation results are recorded in `import_metadata.json`.

The import script does not overwrite an existing checkpoint directory. Use `--output models/model-lain` for another checkpoint, set `INDOBERT_MODEL_DIR` to that location, and restart the backend.

Pretrained IndoBERT supplies the backbone; the imported ZIP must contain a fine-tuned classifier. If no checkpoint is available, use the training script or the notebook runtime export steps below.

## Configuration from the notebook

The source configuration is available in `config/notebook.json`.

| Parameter | Primary notebook value |
| --- | --- |
| Backbone | `indobenchmark/indobert-base-p1` |
| Model | `BertForSequenceClassification` from Transformers |
| Tokenizer | `BertTokenizer` |
| Label indices | `0: positive`, `1: neutral`, `2: negative` |
| Optimizer | `torch.optim.Adam` |
| Learning rate | `3e-6` |
| Epochs | `5` |
| Batch size | `32` |
| Maximum sequence length | `512` |
| Random seed | `42` |
| Training input | Preprocessed TSVs |

The training script ports the notebook's primary run to the CLI, preserving its train/validation loop and final-epoch checkpoint selection. Test data is not used to select parameters. The notebook also contains other learning-rate and epoch experiments; CLI arguments can override these parameters.

```bash
python scripts/train.py --learning-rate 2e-6 --epochs 5
python scripts/train.py --batch-size 8 --device cuda
python scripts/train.py --help
```

Training uses CUDA when available and CPU otherwise. The default worker count is 0 for portability; `--workers 16` is available to match the notebook. CPU training can take considerably longer. Changing the batch size changes training and does not guarantee identical numerical results.

Existing models are preserved unless `--overwrite` is specified. Pretrained model caches and NLTK resources are stored in `.cache/` under the dashboard directory. Use `--local-files-only` for a backbone that has already been downloaded.

## Preprocessing and tokenization consistency

Training and evaluation read the project TSVs directly, without preprocessing them again:

| Split | Original CSV for exploration | IndoBERT input TSV |
| --- | ---: | ---: |
| Train | 7,512 | 7,498 |
| Validation | 2,504 | 2,502 |
| Test | 2,504 | 2,501 |

New dashboard sentences pass through the preprocessing function ported from the notebook, then the IndoBERT tokenizer. TSV evaluation uses only the tokenizer to avoid processing the text twice.

The tokenization adapter follows IndoNLU's `DocumentSentimentDataLoader`: call `tokenizer.encode` with special tokens, retain the prefix up to 512 tokens, pad with ID 0, and create an attention mask. This preserves the notebook's truncation behaviour for long sentences, including the possibility of truncating the final `[SEP]` token. Training and serving use the same adapter.

The original preprocessing pipeline removes slang, stopwords, and English words. This behaviour is preserved for consistency with the training dataset. Some sentiment information may therefore be lost. Preprocessing changes require rebuilding the dataset and fine-tuning again.

## Exporting from a trained notebook runtime

If the trained model is still available in a Colab runtime, export it without retraining. Add the dashboard code directory to the Python path and run the following **after the training run you intend to use**:

```python
import sys
sys.path.insert(0, '/content/dashboard')  # Adjust this to the dashboard code location.
from notebook_export import export_checkpoint

export_checkpoint(
    model,
    tokenizer,
    '/content/indobert-ikn',
    id2label=i2w,
)
```

Copy the entire export directory to `backend/models/indobert-ikn/`. The original notebook uses the names `model`, `tokenizer`, and `i2w`. The default backbone variant, preprocessing profile, and token length match the notebook.

The notebook overwrites `model` in each tuning scenario. Export immediately after the chosen scenario, before starting another one. The export includes `config.json`, `model.safetensors`, tokenizer files, and `serving.json`.

The backend uses local files, verifies label ordering and classifier weight completeness, and runs `model.eval()` and `torch.inference_mode()`. Prediction requests do not download models. Restart the backend after replacing a checkpoint.

An exported checkpoint typically has this structure:

```text
models/indobert-ikn/
  config.json
  model.safetensors
  serving.json
  tokenizer_config.json
  special_tokens_map.json
  vocab.txt
```

Additional files such as `tokenizer.json`, import metadata, and training history may be present depending on how the model was installed. `serving.json` defines the preprocessing profile, tokenization, maximum length, backbone, and label mapping checked by the backend before inference.

## Evaluation and notebook results

The evaluation page provides **Sumber evaluasi** (Evaluation source) with two choices: **Checkpoint proyek** (Project checkpoint, the default) and **Hasil notebook** (Notebook results). Changing the source updates accuracy, Macro F1, test count, confusion matrix, per-class metrics, and the source file. Checkpoint reports also show their evaluation timestamp when available. Accuracy and per-class percentages use two decimal places, while Macro F1 uses four.

The notebook source recalculates metrics from `test_with_predictions new.csv`, containing 2,501 opinions. Accuracy is **77.61%**, and Macro F1 is **0.6393**. These figures come from saved research predictions. If a checkpoint report is missing or does not match the active model, the page explains its status and offers **Lihat hasil notebook** (View notebook results).

`python scripts/evaluate.py` produces the checkpoint evaluation report and a prediction CSV for the topic modelling pipeline.

Checkpoint evaluation outputs:

```text
reports/test.json                  # Accuracy, macro F1, confusion matrix, and per-class metrics.
reports/test_with_predictions.csv  # text, sentiment, sentiment_predict; input for the Top2Vec notebook.
```

The published [checkpoint report](reports/test.json), generated on October 26, 2026, covers all 2,501 opinions in `preprocessed_final_ikn_test.tsv`. The evaluation used CPU inference, batch size 8, the notebook preprocessing profile, and a maximum length of 512 tokens:

| Metric | Installed checkpoint |
| --- | ---: |
| Accuracy | 76.97% |
| Macro F1 | 0.6070 |
| Positive F1 | 0.6041 |
| Neutral F1 | 0.3561 |
| Negative F1 | 0.8608 |

Prediction rows were verified against the source test TSV, and accuracy, Macro F1, confusion matrix, precision, recall, F1, and support were independently checked with scikit-learn. The report contains a SHA-256 model fingerprint. `GET /api/evaluation?source=checkpoint` returns it only when it matches the installed checkpoint; otherwise, rerun evaluation for that model. Both sources are available through the dashboard selector with separate descriptions and provenance.

`reports/test.json` is versioned in Git. The generated `reports/test_with_predictions.csv` remains local and can be recreated by running evaluation. Model weights remain excluded from the repository.

A correction to the notebook: `classification_report(..., target_names=w2i.keys())` without explicit `labels` can swap positive/negative names because alphabetical class ordering differs from IndoNLU ordering. Dashboard calculations use the explicit order **positive → neutral → negative**. Actual test TSV support is 388 positive, 366 neutral, and 1,747 negative opinions.

`test_with_predictions_and_coherence.csv` contains predictions that differ from the first CSV. The topic panel uses the outputs actually saved in the Top2Vec notebook and identifies their source.

## Top2Vec topic modelling

The Next.js topic modelling page provides:

- Positive, neutral, and negative sentiment groups.
- Keywords defining each topic.
- A comparison of `c_v` coherence scores across all three sentiments.
- **Hasil notebook** (Notebook results) and **Hasil training proyek** (Project training results) sources.

The notebook source reads outputs from `../notebooks/Topic_Modelling_of_IKN.ipynb`. To rerun the topic modelling pipeline using IndoBERT predictions:

```bash
python -m pip install -r requirements-topics.txt
python scripts/setup_nltk.py
python scripts/evaluate.py
python scripts/train_topics.py
```

The script follows the notebook: one Top2Vec model per sentiment, `doc2vec` embeddings, `speed='deep-learn'`, `min_count=10`, and gensim `CoherenceModel(coherence='c_v')` evaluation. Models are saved in `models/top2vec/`; the report, topic document counts, and word weights are saved in `reports/topics.json`. Each sentiment group needs at least 20 documents. Small or insufficiently diverse corpora may still fail to form clusters. Top2Vec determines the number of topics from the corpus.

To use an existing prediction CSV without rerunning IndoBERT:

```bash
python scripts/train_topics.py --predictions "../data/predictions/test_with_predictions_and_coherence.csv"
```

Restart the backend after training or replacing models. Open **Analisis kalimat** (Sentence analysis): IndoBERT predicts the sentiment, then `Top2Vec.query_topics` matches the preprocessed text against the model for that sentiment. The interface displays the closest topic, ten keywords, cosine similarity, the topic's document count, and up to two alternative topics. Topic numbers apply within each sentiment group. Topic titles use model keywords rather than manually assigned categories.

Models load on demand and are cached per process. Training does not run during requests. Sentences containing no words recognized by the corpus receive no topic match. If a topic model is missing or fails to load, sentiment prediction still succeeds and the topic section explains the status. Notebook reports do not substitute for inference models.

Topic similarity is a cosine value between −1 and 1, rather than a probability or sentiment confidence score. Even the closest topic may be irrelevant, particularly for short sentences or text outside the IKN context. `c_v` coherence measures word relatedness within the corpus, rather than scoring a new sentence. When available, report keywords include their cosine weights relative to the topic.

Other available commands:

```bash
python scripts/train_topics.py --help
python scripts/train_topics.py --workers 2 --speed learn
```

Changing `--speed` changes training from the notebook configuration. `--overwrite` is required to replace existing model artifacts. Load only local Top2Vec artifacts created or trusted by the project maintainer, because their storage format uses Python deserialization.

API contract:

- `GET /api/health`: IndoBERT status and `topics.groups` for the three Top2Vec models, without loading weights.
- `POST /api/predict` with JSON `{"text":"Opini tentang IKN"}`: sentiment results plus `topic_analysis` (`available`, `matched`, `state`, `sentiment`, `topics`, `message`). Each topic has `number` (starting at 0), `words`, `word_scores`, `similarity`, and `documents`.
- `GET /api/topics?source=notebook|trained`: topic reports for each sentiment. Select **Hasil training proyek** (Project training results) to view newly trained results.

Topic matching follows the [official Top2Vec query_topics API](https://top2vec.readthedocs.io/en/stable/api.html#top2vec.Top2Vec.query_topics).

## Application structure

```text
frontend/             # Next.js App Router, React, TypeScript, and tests
backend/
  server/             # Flask API, inference, datasets, and Top2Vec results
  scripts/            # Setup, training, import, and evaluation
  config/             # Primary notebook configuration
  tests/              # Backend tests
  models/             # Local IndoBERT and Top2Vec checkpoints
  reports/            # Evaluation and generated reports
  run.py              # Flask entrypoint
compose.yaml          # Docker services, run from the repository root
```

The IndoBERT checkpoint directory is `models/indobert-ikn/`.

Some notebook learning-rate experiment outputs differ from the saved source cells. Application training follows the primary run's source (`3e-6`, 5 epochs), while historical metrics are calculated from the actual CSVs.

## Environment variables

The backend reads variables from the process environment and does not automatically load `.env` files. Default paths are resolved from the repository location; use absolute paths for custom settings. The frontend reads `FLASK_API_URL` through the Next.js environment, such as `frontend/.env.local` copied from `.env.example`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `INDOBERT_MODEL_DIR` | `backend/models/indobert-ikn` | Fine-tuned checkpoint |
| `IKN_DATA_DIR` | `data/` at the repository root | Contains `raw/`, `processed/`, `external/`, and `predictions/` |
| `IKN_NOTEBOOKS_DIR` | `notebooks/` at the repository root | Original notebooks and saved topic outputs |
| `INDOBERT_DEVICE` | `cpu` | Serving device: `cpu` or `cuda` |
| `TOP2VEC_MODEL_DIR` | `backend/models/top2vec` | Three local Top2Vec models; also used by the training CLI |
| `TOP2VEC_REPORT_DIR` | `backend/reports` | Directory containing `topics.json`; also used by the training CLI |
| `PORT` | `5000` | Local Flask port |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend origin allowed to submit predictions |
| `IKN_TRUSTED_HOSTS` | `localhost,127.0.0.1,[::1]` | Comma-separated list of accepted backend hosts |
| `FLASK_API_URL` | `http://127.0.0.1:5000` | Flask URL used by the Next.js proxy |

## Testing

```bash
python -m unittest discover -s tests -v
cd ../frontend
npm run typecheck
npm test
npm run build
npm run test:render
```

Tests cover the original data, notebook outputs, label ordering, cleaning, IndoNLU token truncation, CSV metrics, Flask API contracts, topic reports, and frontend proxy/request behaviour. Topic integration tests use a test double matching the Top2Vec contract to check model selection, caching, unknown vocabulary, invalid cosine values, and sentiment results when Top2Vec is unavailable. Component rendering tests check topic results, fallbacks, escaping, and the distinction between cosine values and percentages. API tests require Flask. Verifying real Top2Vec training and inference requires its dependencies and model artifacts.

`test:render` checks production rendering for all five pages, active sidebar links, page content isolation, topic and evaluation source selectors, per-page CSP nonces, script nonces, and headers without opening a network port. Run it after a build. This check does not replace visual and interaction testing in a browser.

Predictions run when **Analisis kalimat** (Analyze sentence) is selected, with a 2,000-character input limit, one active inference per backend process, and 30 attempts per minute per process. Excess requests receive HTTP 429, and a busy model returns HTTP 503. Both responses include `Retry-After`.

The workspace uses a cream white palette, sage accents for primary actions, and distinct colours for each sentiment.

## References

- [IndoNLU source: datasets and data loaders](https://github.com/IndoNLP/indonlu/blob/master/utils/data_utils.py)
- [IndoNLU fine-tuning guide](https://github.com/IndoNLP/indonlu/wiki/Quickstart-~-Fine-Tune)
- [Pretrained IndoBERT base p1](https://huggingface.co/indobenchmark/indobert-base-p1)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Next.js API rewrites](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites)
- [Top2Vec](https://github.com/ddangelov/Top2Vec)

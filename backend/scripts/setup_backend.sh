#!/usr/bin/env bash
# Install the backend and verify the local checkpoint without starting a server.
set -euo pipefail

ikn_dashboard_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ikn_dashboard_dir"
ikn_python="${IKN_SETUP_PYTHON:-python3}"
ikn_venv_python="$ikn_dashboard_dir/.venv/bin/python"

"$ikn_python" -c 'import sys; sys.exit("Gunakan Python 3.10 atau lebih baru.") if sys.version_info < (3, 10) else None'
mkdir -p .cache/pip .cache/wheels

if [[ ! -x "$ikn_venv_python" || ! -f .venv/bin/activate ]]; then
    "$ikn_python" -m venv --without-pip .venv
fi

if ! "$ikn_venv_python" -m pip --version >/dev/null 2>&1; then
    if "$ikn_venv_python" -c 'import ensurepip' >/dev/null 2>&1; then
        "$ikn_venv_python" -m ensurepip --upgrade
    elif "$ikn_python" -m pip --version >/dev/null 2>&1; then
        "$ikn_python" -m pip --python "$ikn_venv_python" install \
            --cache-dir .cache/pip --find-links .cache/wheels pip
    else
        printf '%s\n' 'pip belum tersedia. Pasang python3-pip atau gunakan Python dengan ensurepip, lalu jalankan ulang skrip ini.' >&2
        exit 1
    fi
fi

# Serving defaults to CPU; select the CPU wheel on Linux to avoid CUDA downloads.
if [[ "$(uname -s)" == Linux ]]; then
    "$ikn_venv_python" -m pip install --disable-pip-version-check \
        --cache-dir .cache/pip --find-links .cache/wheels \
        --index-url https://download.pytorch.org/whl/cpu 'torch>=2.6,<3'
fi
"$ikn_venv_python" -m pip install --disable-pip-version-check \
    --cache-dir .cache/pip --find-links .cache/wheels -r requirements.txt
"$ikn_venv_python" -m pip --cache-dir .cache/pip check
"$ikn_venv_python" scripts/setup_nltk.py
"$ikn_venv_python" -m unittest discover -s tests -v

"$ikn_venv_python" - <<'PY'
from server import create_app

client = create_app({'TESTING': True}).test_client()
summary = client.get('/api/summary')
if summary.status_code != 200:
    raise SystemExit(f'Pembacaan dataset gagal: {summary.get_json()}')
prediction = client.post('/api/predict', json={'text': 'Saya mendukung pembangunan ibu kota Nusantara.'})
if prediction.status_code != 200:
    raise SystemExit(f'Prediksi IndoBERT gagal: {prediction.get_json()}')
result = prediction.get_json()
print(f"Dataset: {summary.get_json()['total']} opini; prediksi IndoBERT: {result['label']} ({result['confidence']:.2%}).")
PY

printf '\n%s\n' 'Backend siap. Jalankan dari folder backend: .venv/bin/python run.py'

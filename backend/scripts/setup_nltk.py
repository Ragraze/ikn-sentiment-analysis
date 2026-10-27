"""Run once, only if the exported notebook uses the 'notebook' preprocessing profile."""
import nltk
from pathlib import Path

target = Path(__file__).resolve().parents[1] / '.cache/nltk'
target.mkdir(parents=True, exist_ok=True)

for resource in ('punkt_tab', 'words'):
    if not nltk.download(resource, download_dir=str(target), raise_on_error=True):
        raise SystemExit(f'Tidak dapat mengunduh resource NLTK: {resource}')
print('Resource preprocessing notebook siap.')

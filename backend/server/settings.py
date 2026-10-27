import json
import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = APP_DIR.parent
DATA_DIR = Path(os.environ.get('IKN_DATA_DIR', PROJECT_DIR / 'data'))
NOTEBOOKS_DIR = Path(os.environ.get('IKN_NOTEBOOKS_DIR', PROJECT_DIR / 'notebooks'))
NOTEBOOK = json.loads((APP_DIR / 'config/notebook.json').read_text(encoding='utf-8'))
ID2LABEL = {int(index): label for index, label in NOTEBOOK['id2label'].items()}
LABEL2ID = {label: index for index, label in ID2LABEL.items()}


def data_file(root: Path, category: str, filename: str) -> Path:
    """Resolve grouped data; accept flat directories supplied by existing integrations."""
    grouped = root / category / filename
    legacy = root / filename
    return legacy if not grouped.is_file() and legacy.is_file() else grouped

"""Call this from the original training notebook after fine-tuning has completed."""
import json
from pathlib import Path

from server.inference import ALIASES
from server.settings import NOTEBOOK, ID2LABEL


def export_checkpoint(model, tokenizer, output_dir, *, id2label=None, preprocessing=NOTEBOOK['preprocessing'],
                      max_length=NOTEBOOK['max_length'], base_model=NOTEBOOK['base_model']):
    """Export the existing model, never create/train a substitute classifier.

    Defaults are verified against Sentimen_Analysis_IKN_IndoBERT.ipynb.
    """
    if model.config.model_type != 'bert' or model.config.num_labels != 3:
        raise ValueError('Model harus IndoBERT/BERT dengan classifier tiga label.')
    mapping = ID2LABEL if id2label is None else id2label
    labels = {int(index): ALIASES[label.lower()] for index, label in mapping.items()}
    if set(labels) != {0, 1, 2} or set(labels.values()) != {'positive', 'negative', 'neutral'}:
        raise ValueError('Gunakan mapping label asli dari notebook, lengkap untuk indeks 0, 1, 2.')
    if preprocessing not in ('raw', 'notebook'):
        raise ValueError('Pilih raw atau notebook sesuai input saat fine-tuning.')
    if not isinstance(max_length, int) or not 2 <= max_length <= 512:
        raise ValueError('max_length harus sesuai notebook dan berada pada rentang 2–512.')
    if not isinstance(base_model, str) or not base_model.strip():
        raise ValueError('Isi ID backbone pretrained yang dipakai notebook.')
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model.config.id2label = labels
    model.config.label2id = {label: index for index, label in labels.items()}
    model.save_pretrained(output, safe_serialization=True)
    tokenizer.save_pretrained(output)
    manifest = dict(task='sentiment-classification', base_model=base_model, id2label=labels,
                    preprocessing=preprocessing, max_length=max_length, tokenization='indonlu-prefix',
                    notebook=NOTEBOOK['source'], notebook_sha256=NOTEBOOK['source_sha256'])
    (output / 'serving.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return output.resolve()

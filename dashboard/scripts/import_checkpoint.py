"""Install a Colab save_pretrained ZIP without loading or retraining its weights."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import sys
import tempfile
import zipfile

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from server.settings import ID2LABEL, NOTEBOOK

MAX_ARCHIVE_FILES = 128
MAX_ARCHIVE_BYTES = 2 * 1024 ** 3
MAX_FILE_BYTES = 1024 ** 3
ALLOWED_FILES = {'config.json', 'model.safetensors', 'tokenizer.json',
                 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt'}


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_weights(path, config):
    """Check safetensors boundaries and classification dimensions using its JSON header."""
    with path.open('rb') as source:
        prefix = source.read(8)
        if len(prefix) != 8:
            raise ValueError('Header safetensors tidak lengkap.')
        size = struct.unpack('<Q', prefix)[0]
        if not 2 <= size <= 20_000_000:
            raise ValueError('Ukuran header safetensors tidak valid.')
        header = json.loads(source.read(size))
    data_size = path.stat().st_size - 8 - size
    byte_sizes = {'F64': 8, 'F32': 4, 'F16': 2, 'BF16': 2, 'I64': 8, 'I32': 4,
                  'I16': 2, 'I8': 1, 'U64': 8, 'U32': 4, 'U16': 2, 'U8': 1, 'BOOL': 1}
    intervals = []
    dtypes = Counter()
    for name, tensor in header.items():
        if name == '__metadata__':
            continue
        start, end = tensor['data_offsets']
        shape, dtype = tensor['shape'], tensor['dtype']
        if dtype not in byte_sizes or any(not isinstance(value, int) or value < 0 for value in shape):
            raise ValueError(f'Tipe atau shape tensor tidak didukung: {name}.')
        if not 0 <= start <= end <= data_size or end - start != math.prod(shape) * byte_sizes[dtype]:
            raise ValueError(f'Ukuran tensor tidak cocok dengan data: {name}.')
        intervals.append((start, end))
        dtypes[dtype] += 1
    cursor = 0
    for start, end in sorted(intervals):
        if start != cursor:
            raise ValueError('Data tensor safetensors tumpang tindih atau tidak lengkap.')
        cursor = end
    if cursor != data_size:
        raise ValueError('Panjang file bobot tidak cocok dengan header safetensors.')
    hidden = config['hidden_size']
    required = {
        'classifier.weight': [3, hidden], 'classifier.bias': [3],
        'bert.embeddings.word_embeddings.weight': [config['vocab_size'], hidden],
        'bert.embeddings.position_embeddings.weight': [config['max_position_embeddings'], hidden],
    }
    for name, expected in required.items():
        if header.get(name, {}).get('shape') != expected:
            raise ValueError(f'Bobot {name} tidak sesuai classifier IndoBERT tiga kelas: diharapkan {expected}.')
    return dict(tensor_count=len(intervals), dtypes=dict(dtypes), classifier_shape=header['classifier.weight']['shape'])


def prepare_tokenizer(directory, config):
    tokenizer_file = directory / 'tokenizer.json'
    if not tokenizer_file.is_file():
        raise ValueError('ZIP memerlukan tokenizer.json agar urutan vocabulary hasil training dapat diverifikasi.')
    tokenizer = json.loads(tokenizer_file.read_text())
    model = tokenizer.get('model', {})
    if model.get('type') != 'WordPiece':
        raise ValueError('Tokenizer harus WordPiece sesuai BertTokenizer pada notebook.')
    vocab = model.get('vocab', {})
    if not vocab or set(vocab.values()) != set(range(len(vocab))):
        raise ValueError('Indeks vocabulary harus unik dan berurutan dari 0.')
    if len(vocab) > config['vocab_size']:
        raise ValueError('Indeks vocabulary melebihi jumlah embedding pada checkpoint.')
    special = {name: vocab.get(name) for name in ('[PAD]', '[UNK]', '[CLS]', '[SEP]', '[MASK]')}
    if special != {'[PAD]': 0, '[UNK]': 1, '[CLS]': 2, '[SEP]': 3, '[MASK]': 4}:
        raise ValueError('ID special token berbeda dari tokenizer IndoBERT notebook.')
    ordered = [token for token, _ in sorted(vocab.items(), key=lambda item: item[1])]
    if any('\n' in token or '\r' in token for token in ordered):
        raise ValueError('Vocabulary mengandung token baris baru yang tidak kompatibel.')
    vocab_file = directory / 'vocab.txt'
    if vocab_file.exists():
        if vocab_file.read_text().splitlines() != ordered:
            raise ValueError('vocab.txt dan tokenizer.json memiliki urutan token yang berbeda.')
    else:
        vocab_file.write_text('\n'.join(ordered) + '\n')
    config_path = directory / 'tokenizer_config.json'
    tokenizer_config = json.loads(config_path.read_text()) if config_path.is_file() else {}
    if tokenizer_config.get('do_lower_case', True) is not True:
        raise ValueError('Tokenizer harus uncased seperti pretrained IndoBERT notebook.')
    tokenizer_config.update(tokenizer_class='BertTokenizer', model_max_length=NOTEBOOK['max_length'], do_lower_case=True)
    config_path.write_text(json.dumps(tokenizer_config, indent=2) + '\n')
    (directory / 'special_tokens_map.json').write_text(json.dumps({
        'unk_token': '[UNK]', 'sep_token': '[SEP]', 'pad_token': '[PAD]',
        'cls_token': '[CLS]', 'mask_token': '[MASK]',
    }, indent=2) + '\n')
    return dict(vocabulary_size=len(vocab), embedding_rows=config['vocab_size'], special_token_ids=special)


def import_checkpoint(archive_path, destination):
    archive_path, destination = Path(archive_path).resolve(), Path(destination).resolve()
    if not archive_path.is_file():
        raise ValueError('File ZIP checkpoint tidak ditemukan.')
    if archive_path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError('File ZIP checkpoint melebihi batas ukuran 2 GiB.')
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Folder tujuan sudah berisi model. Pilih --output lain agar checkpoint yang ada tetap tersimpan.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_hash = file_hash(archive_path)
    with tempfile.TemporaryDirectory(prefix='.checkpoint-import-', dir=destination.parent) as temporary:
        staging = Path(temporary) / 'checkpoint'
        staging.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_FILES or sum(entry.file_size for entry in entries) > MAX_ARCHIVE_BYTES:
                raise ValueError('ZIP checkpoint melebihi batas jumlah file atau ukuran ekstraksi.')
            roots = [PurePosixPath(entry.filename).parent for entry in entries
                     if PurePosixPath(entry.filename).name == 'config.json' and not entry.is_dir()]
            if len(roots) != 1:
                raise ValueError('ZIP harus memuat tepat satu config.json checkpoint.')
            root = roots[0]
            extracted = set()
            for entry in entries:
                name = PurePosixPath(entry.filename)
                if name.is_absolute() or '..' in name.parts or '\\' in entry.filename:
                    raise ValueError('Path arsip tidak valid.')
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError('ZIP checkpoint tidak boleh memuat symbolic link.')
                if entry.is_dir() or not name.is_relative_to(root):
                    continue
                relative = name.relative_to(root)
                if relative.as_posix() not in ALLOWED_FILES:
                    raise ValueError('ZIP hanya boleh berisi bobot safetensors dan konfigurasi tokenizer/checkpoint.')
                if entry.file_size > MAX_FILE_BYTES or entry.flag_bits & 1:
                    raise ValueError('Ukuran atau enkripsi file ZIP tidak didukung.')
                if relative in extracted:
                    raise ValueError('ZIP mengandung path file duplikat.')
                extracted.add(relative)
                target = staging.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, target.open('wb') as output:
                    # Reading each stream to its end also verifies the ZIP CRC.
                    shutil.copyfileobj(source, output, length=1024 * 1024)
        config_file = staging / 'config.json'
        original_config = json.loads(config_file.read_text())
        config = dict(original_config)
        if config.get('model_type') != 'bert' or config.get('architectures') != ['BertForSequenceClassification']:
            raise ValueError('Checkpoint harus BertForSequenceClassification seperti notebook.')
        current_labels = config.get('id2label', {})
        expected = {str(index): label for index, label in ID2LABEL.items()}
        generic = {str(index): f'LABEL_{index}' for index in ID2LABEL}
        if current_labels not in (expected, generic):
            raise ValueError('Mapping label checkpoint berbeda dari notebook; periksa label training sebelum memasangnya.')
        weights = staging / 'model.safetensors'
        if not weights.is_file():
            raise ValueError('Import ZIP ini memerlukan model.safetensors hasil save_pretrained.')
        tensor_info = inspect_weights(weights, config)
        tokenizer_info = prepare_tokenizer(staging, config)
        (staging / 'config.original.json').write_text(json.dumps(original_config, indent=2) + '\n')
        config.pop('_num_labels', None)
        config.update(num_labels=3, id2label=expected, label2id={label: index for index, label in ID2LABEL.items()})
        config_file.write_text(json.dumps(config, indent=2) + '\n')
        manifest = dict(task='sentiment-classification', base_model=NOTEBOOK['base_model'], id2label=expected,
                        preprocessing=NOTEBOOK['preprocessing'], max_length=NOTEBOOK['max_length'],
                        tokenization=NOTEBOOK['tokenization'], notebook=NOTEBOOK['source'],
                        notebook_sha256=NOTEBOOK['source_sha256'], source_archive=archive_path.name,
                        source_archive_sha256=source_hash)
        (staging / 'serving.json').write_text(json.dumps(manifest, indent=2) + '\n')
        report = dict(source_archive=archive_path.name, source_archive_sha256=source_hash,
                      installed_at=datetime.now(timezone.utc).isoformat(),
                      weights_sha256=file_hash(weights), weights_bytes=weights.stat().st_size,
                      label_mapping_source=NOTEBOOK['source'], **tensor_info, **tokenizer_info)
        (staging / 'import_metadata.json').write_text(json.dumps(report, indent=2) + '\n')
        if destination.exists():
            destination.rmdir()  # Only the empty directory permitted above.
        staging.rename(destination)
    return report


def main():
    parser = argparse.ArgumentParser(description='Pasang ZIP IndoBERT dari Colab ke backend Flask tanpa training ulang.')
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, default=APP / 'models/indobert-ikn')
    args = parser.parse_args()
    try:
        report = import_checkpoint(args.archive, args.output)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f'Checkpoint belum dipasang: {error}\n')
    print(json.dumps(dict(destination=str(args.output.resolve()), **report), indent=2))


if __name__ == '__main__':
    main()

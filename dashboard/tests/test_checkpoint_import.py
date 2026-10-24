"""Small synthetic archive fixtures test packaging, not neural inference."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from scripts.import_checkpoint import import_checkpoint, file_hash
from server.inference import IndoBertService, read_manifest
from unittest.mock import patch


def sample_archive(path, *, prefix='', classifier_size=3, unsafe=False, conflicting_labels=False):
    config = dict(model_type='bert', architectures=['BertForSequenceClassification'], hidden_size=2,
                  vocab_size=8, max_position_embeddings=8, _num_labels=5,
                  id2label={str(i): f'LABEL_{i}' for i in range(3)})
    if conflicting_labels:
        config['id2label'] = {'0': 'negative', '1': 'neutral', '2': 'positive'}
    shapes = {'classifier.weight': [classifier_size, 2], 'classifier.bias': [classifier_size],
              'bert.embeddings.word_embeddings.weight': [8, 2],
              'bert.embeddings.position_embeddings.weight': [8, 2]}
    header, offset = {}, 0
    for name, shape in shapes.items():
        end = offset + shape[0] * (shape[1] if len(shape) > 1 else 1) * 4
        header[name] = dict(dtype='F32', shape=shape, data_offsets=[offset, end])
        offset = end
    encoded = json.dumps(header).encode()
    encoded += b' ' * ((8 - len(encoded) % 8) % 8)
    weights = struct.pack('<Q', len(encoded)) + encoded + bytes(offset)
    tokens = ['[PAD]', '[UNK]', '[CLS]', '[SEP]', '[MASK]', 'ikn']
    tokenizer = dict(model=dict(type='WordPiece', vocab={token: i for i, token in enumerate(tokens)}))
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(prefix + 'config.json', json.dumps(config))
        archive.writestr(prefix + 'tokenizer.json', json.dumps(tokenizer))
        archive.writestr(prefix + 'tokenizer_config.json', json.dumps(dict(do_lower_case=True)))
        archive.writestr(prefix + 'model.safetensors', weights)
        if unsafe:
            archive.writestr('../outside.txt', 'must not be written')
    return weights


class ImportCheckpointTests(unittest.TestCase):
    def test_colab_zip_becomes_the_configured_backend_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / 'model.zip'
            original_weights = sample_archive(archive)
            source_hash = file_hash(archive)
            destination = root / 'models/indobert-ikn'
            report = import_checkpoint(archive, destination)
            manifest, labels = read_manifest(destination)
            self.assertEqual(labels, {0: 'positive', 1: 'neutral', 2: 'negative'})
            self.assertEqual(manifest['tokenization'], 'indonlu-prefix')
            self.assertEqual(IndoBertService(destination).status()['state'], 'configured')
            self.assertEqual((destination / 'model.safetensors').read_bytes(), original_weights)
            self.assertEqual(file_hash(archive), source_hash)
            self.assertEqual(report['source_archive_sha256'], source_hash)
            self.assertEqual(report['classifier_shape'], [3, 2])
            self.assertEqual((destination / 'vocab.txt').read_text().splitlines(),
                             ['[PAD]', '[UNK]', '[CLS]', '[SEP]', '[MASK]', 'ikn'])
            config = json.loads((destination / 'config.json').read_text())
            self.assertEqual(config['num_labels'], 3)
            self.assertNotIn('_num_labels', config)
            self.assertEqual(json.loads((destination / 'config.original.json').read_text())['_num_labels'], 5)

    def test_nested_export_directory_is_flattened(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample_archive(root / 'model.zip', prefix='colab/indobert_model/')
            import_checkpoint(root / 'model.zip', root / 'installed')
            self.assertTrue((root / 'installed/config.json').is_file())

    def test_mismatched_classifier_or_labels_do_not_publish_a_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for options in [dict(classifier_size=2), dict(conflicting_labels=True)]:
                sample_archive(root / 'model.zip', **options)
                with self.assertRaises(ValueError):
                    import_checkpoint(root / 'model.zip', root / 'installed')
                self.assertFalse((root / 'installed').exists())

    def test_existing_checkpoint_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample_archive(root / 'model.zip')
            target = root / 'installed'
            target.mkdir()
            (target / 'existing.txt').write_text('preserve')
            with self.assertRaises(ValueError):
                import_checkpoint(root / 'model.zip', target)
            self.assertEqual((target / 'existing.txt').read_text(), 'preserve')

    def test_archive_paths_cannot_write_outside_the_model_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample_archive(root / 'model.zip', unsafe=True)
            with self.assertRaises(ValueError):
                import_checkpoint(root / 'model.zip', root / 'models/installed')
            self.assertFalse((root / 'models/outside.txt').exists())
            self.assertFalse((root / 'models/installed').exists())

    def test_oversized_archive_and_executable_payloads_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample_archive(root / 'model.zip')
            with patch('scripts.import_checkpoint.MAX_ARCHIVE_BYTES', 1):
                with self.assertRaises(ValueError):
                    import_checkpoint(root / 'model.zip', root / 'installed')
            with zipfile.ZipFile(root / 'model.zip', 'a') as archive:
                archive.writestr('custom_model.py', 'raise RuntimeError("must not run")')
            with self.assertRaises(ValueError):
                import_checkpoint(root / 'model.zip', root / 'installed')
            self.assertFalse((root / 'installed').exists())

    def test_symlinks_and_duplicate_paths_are_rejected(self):
        import stat
        import warnings
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for duplicate in (False, True):
                sample_archive(root / 'model.zip')
                with zipfile.ZipFile(root / 'model.zip', 'a') as archive:
                    if duplicate:
                        with warnings.catch_warnings():
                            warnings.simplefilter('ignore', UserWarning)
                            archive.writestr('tokenizer.json', '{}')
                    else:
                        entry = zipfile.ZipInfo('vocab.txt')
                        entry.create_system = 3
                        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                        archive.writestr(entry, '/etc/passwd')
                with self.assertRaises(ValueError):
                    import_checkpoint(root / 'model.zip', root / 'installed')
                self.assertFalse((root / 'installed').exists())


if __name__ == '__main__':
    unittest.main()

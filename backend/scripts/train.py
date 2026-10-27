"""Port the primary IndoBERT fine-tuning run from the original notebook to a CLI."""
import argparse
import json
import os
from pathlib import Path
import random
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from notebook_export import export_checkpoint
from server.data import DatasetRepository
from server.metrics import calculate_metrics
from server.settings import DATA_DIR, ID2LABEL, LABEL2ID, NOTEBOOK
from server.tokenization import encode_batch, to_tensors


class NotebookCollator:
    def __init__(self, tokenizer, max_length):
        self.tokenizer, self.max_length = tokenizer, max_length

    def __call__(self, batch):
        encoded = encode_batch(self.tokenizer, [row['text'] for row in batch], self.max_length)
        return encoded, [LABEL2ID[row['label']] for row in batch]


def main():
    parser = argparse.ArgumentParser(description='Fine-tune indobenchmark/indobert-base-p1 sesuai notebook IKN.')
    parser.add_argument('--data-dir', default=str(DATA_DIR))
    parser.add_argument('--model-dir', default=os.environ.get('INDOBERT_MODEL_DIR', str(APP / 'models/indobert-ikn')))
    parser.add_argument('--base-model', default=NOTEBOOK['base_model'], help='Hugging Face model ID atau backbone lokal.')
    parser.add_argument('--epochs', type=int, default=NOTEBOOK['epochs'])
    parser.add_argument('--learning-rate', type=float, default=NOTEBOOK['learning_rate'])
    parser.add_argument('--batch-size', type=int, default=NOTEBOOK['batch_size'])
    parser.add_argument('--max-length', type=int, default=NOTEBOOK['max_length'])
    parser.add_argument('--seed', type=int, default=NOTEBOOK['seed'])
    parser.add_argument('--device', default='auto', help='auto, cpu, atau cuda')
    parser.add_argument('--workers', type=int, default=0)
    parser.add_argument('--local-files-only', action='store_true', help='Gunakan cache/backbone lokal tanpa unduhan.')
    parser.add_argument('--overwrite', action='store_true', help='Izinkan menimpa checkpoint pada model-dir.')
    args = parser.parse_args()
    if args.epochs < 1 or args.learning_rate <= 0 or not 1 <= args.batch_size <= 128 or not 2 <= args.max_length <= 512 or args.workers < 0:
        parser.error('Epoch/lr harus positif, batch size 1–128, max length 2–512, workers >= 0.')
    output = Path(args.model_dir)
    if output.exists() and any(output.iterdir()) and not args.overwrite:
        parser.error('model-dir sudah berisi file. Pilih folder lain atau gunakan --overwrite.')
    os.environ.setdefault('HF_HOME', str(APP / '.cache/huggingface'))
    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    from transformers import BertConfig, BertForSequenceClassification, BertTokenizer

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    device = ('cuda' if torch.cuda.is_available() else 'cpu') if args.device == 'auto' else args.device
    if device == 'cuda' and not torch.cuda.is_available():
        parser.error('CUDA tidak tersedia; gunakan --device cpu atau pasang PyTorch CUDA.')
    repository = DatasetRepository(Path(args.data_dir))
    train_rows, validation_rows = repository.preprocessed('train'), repository.preprocessed('val')
    tokenizer = BertTokenizer.from_pretrained(args.base_model, local_files_only=args.local_files_only)
    config = BertConfig.from_pretrained(args.base_model, local_files_only=args.local_files_only,
                                        num_labels=3, id2label=ID2LABEL, label2id=LABEL2ID)
    model = BertForSequenceClassification.from_pretrained(args.base_model, config=config,
                                                        local_files_only=args.local_files_only).to(device)
    # Like notebook cell 18: Adam, not AdamW; no scheduler or class weighting.
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)

    collate = NotebookCollator(tokenizer, args.max_length)
    train_loader = DataLoader(train_rows, batch_size=args.batch_size, shuffle=True, num_workers=args.workers, collate_fn=collate)
    val_loader = DataLoader(validation_rows, batch_size=args.batch_size, shuffle=False, num_workers=args.workers, collate_fn=collate)

    def epoch(loader, training):
        model.train(training)
        total_loss, truth, predicted = 0.0, [], []
        context = torch.enable_grad() if training else torch.inference_mode()
        with context:
            for step, (encoded, targets) in enumerate(loader, 1):
                tensors = to_tensors(torch, encoded, device)
                targets_tensor = torch.tensor(targets, dtype=torch.long, device=device)
                if training:
                    optimizer.zero_grad()
                outputs = model(**tensors, labels=targets_tensor, return_dict=True)
                if training:
                    outputs.loss.backward()
                    optimizer.step()
                total_loss += outputs.loss.item()
                truth.extend(ID2LABEL[index] for index in targets)
                predicted.extend(ID2LABEL[index] for index in outputs.logits.argmax(dim=-1).detach().cpu().tolist())
                if step % 25 == 0:
                    print(f'{"TRAIN" if training else "VALID"} {step}/{len(loader)} loss={total_loss / step:.4f}', flush=True)
        return dict(loss=total_loss / len(loader), **calculate_metrics(truth, predicted))

    history = []
    print(f'Backbone={args.base_model}; device={device}; train={len(train_rows)}; validation={len(validation_rows)}', flush=True)
    for number in range(1, args.epochs + 1):
        train = epoch(train_loader, True)
        validation = epoch(val_loader, False)
        history.append(dict(epoch=number, train=train, validation=validation))
        print(f'Epoch {number}/{args.epochs}: train_acc={train["accuracy"]:.4f}; val_acc={validation["accuracy"]:.4f}; val_macro_f1={validation["macro_f1"]:.4f}', flush=True)
    # Preserve the original primary run's final-epoch behavior. Test is evaluated separately.
    model.to('cpu')
    export_checkpoint(model, tokenizer, output, id2label=ID2LABEL,
                      max_length=args.max_length, base_model=args.base_model, preprocessing='notebook')
    (output / 'training_history.json').write_text(json.dumps(dict(
        parameters=vars(args), selected_epoch=args.epochs, selection='final_epoch_as_in_notebook', history=history), indent=2))
    print(f'Checkpoint terlatih tersimpan: {output.resolve()}')
    print('Berikutnya: python scripts/setup_nltk.py && python scripts/evaluate.py && python run.py')


if __name__ == '__main__':
    main()

"""Match IndoNLU's encode -> prefix slice -> zero pad sequence loader.

Source: https://github.com/IndoNLP/indonlu/blob/master/utils/data_utils.py
Kept as a small adapter so the application does not need a cloned research repo.
"""


def encode_batch(tokenizer, texts, max_length=512):
    if not texts:
        raise ValueError('Batch teks tidak boleh kosong.')
    if tokenizer.pad_token_id != 0:
        raise ValueError('Tokenizer notebook IndoNLU memerlukan padding token ID 0.')
    sequences = [tokenizer.encode(text, add_special_tokens=True, truncation=False)[:max_length] for text in texts]
    width = max(map(len, sequences))
    return {
        'input_ids': [sequence + [0] * (width - len(sequence)) for sequence in sequences],
        'attention_mask': [[1.0] * len(sequence) + [0.0] * (width - len(sequence)) for sequence in sequences],
    }


def to_tensors(torch, encoded, device='cpu'):
    return {
        'input_ids': torch.tensor(encoded['input_ids'], dtype=torch.long, device=device),
        'attention_mask': torch.tensor(encoded['attention_mask'], dtype=torch.float32, device=device),
    }

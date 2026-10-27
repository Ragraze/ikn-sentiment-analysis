"""Serving preprocessing is explicitly exported from the training notebook."""
from functools import lru_cache
from pathlib import Path
import csv
import re
from .settings import data_file


def cleaning_text(text):
    # Matches cell 10 in Preprocessing_Datasets_IKN.ipynb, including its order.
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'http[s]?\:\/\/[a-zA-Z0-9\.\/\_?=%&#\-\+!]+', ' ', text)
    text = re.sub(r'pic.twitter.com?[a-zA-Z0-9\.\/\_?=%&#\-\+!]+', ' ', text)
    text = re.sub(r'\@([\w]+)', ' ', text)
    text = re.sub(r'\#([\w]+)', ' ', text)
    text = re.sub(r'''[!$%^&*@#()_+|~=`{}\[\]%\-:";'<>?,.\/]''', ' ', text)
    text = re.sub(r'[0-9]+', '', text)
    text = re.sub(r'([a-zA-Z])\1{2,}', r'\1', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'^[ ]|[ ]$', '', text)
    return text.lower()


class Preprocessor:
    def __init__(self, profile, data_dir: Path):
        if profile not in ('raw', 'notebook'):
            raise ValueError('preprocessing harus raw atau notebook sesuai data training.')
        self.profile = profile
        if profile == 'notebook':
            import nltk
            nltk.data.path.insert(0, str(Path(__file__).resolve().parents[1] / '.cache/nltk'))
            from nltk.corpus import words
            from nltk.tokenize import word_tokenize
            from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
            self.tokenize = word_tokenize
            self.tokenize('cek resource tokenizer')  # Fail at setup when punkt_tab is absent.
            self.english_words = set(words.words())
            stopwords = data_file(data_dir, 'external', 'Kamus_id.stopwords.02.01.2016 custom.txt')
            self.stopwords = set(stopwords.read_text(encoding='utf-8').splitlines())
            slang = data_file(data_dir, 'external', 'Kamus_colloquial-indonesian-lexicon.csv')
            with slang.open(encoding='utf-8-sig', newline='') as source:
                self.slang = {row['slang'] for row in csv.DictReader(source)}
            self.stem = lru_cache(maxsize=100_000)(StemmerFactory().create_stemmer().stem)

    def __call__(self, text):
        if self.profile == 'raw':
            return text.strip()
        tokens = self.tokenize(cleaning_text(text))
        # Keep the notebook's word removal order to match the trained checkpoint.
        return ' '.join(self.stem(word) for word in tokens if word.lower() not in self.slang
                        and word.lower() not in self.stopwords and word.lower() not in self.english_words)

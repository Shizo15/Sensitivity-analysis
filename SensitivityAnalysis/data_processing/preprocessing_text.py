# data_processing/preprocessing_text.py

# StopWords
from spacy.lang.en.stop_words import STOP_WORDS
import re
import spacy
from string import punctuation

stopwords_set = set(STOP_WORDS)
exclude_words = {'no', 'not', 'never', 'neither', 'nor', 'none', 'cannot'}
final_stopwords = list(stopwords_set - exclude_words)


def clean_text(text):
    text = str(text)
    temp = text.lower()
    temp = re.sub(r'<[^>]*>', '', temp)
    emojis = re.findall(r'(?::|;|=)(?:-)?(?:\)|\(|D|P)', temp)
    temp = re.sub(r'[^a-zA-Z\s]', ' ', temp)
    temp = temp + ' ' + ' '.join(emojis).replace('-', '')
    temp = re.sub(r'\s+', ' ', temp).strip()

    return temp

# Lematization:
try:
    nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])
except OSError:
    print("Pobieranie modelu językowego spaCy (en_core_web_sm)...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])

#Final function
def text_tokenizer(text):
    cleaned_text = clean_text(text)
    doc = nlp(cleaned_text)
    lemmas = [token.lemma_ for token in doc]
    return [lemma for lemma in lemmas if lemma not in final_stopwords and len(lemma) > 2]
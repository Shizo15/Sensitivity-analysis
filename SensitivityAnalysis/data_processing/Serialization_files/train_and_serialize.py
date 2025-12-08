# train_and_serialize.py

import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

# 🎯 KLUCZOWA ZMIANA: Importujemy funkcję z jej stałego modułu.
from data_processing.preprocessing_text import text_tokenizer

# ----------------------------------------------------------------------
# 1. ŁADOWANIE I PRZYGOTOWANIE DANYCH (symulacja Colab)
# ----------------------------------------------------------------------

# ⚠️ ZAŁADUJ SWÓJ ZBIÓR DANYCH TUTAJ!
path = '../colab_train_models/Data/1_training_data_high_quality.csv'
try:
    df = pd.read_csv(path)
    # Używam poniższych nazw kolumn jako domyślnych z kodu Colaba:
    df = df.rename(columns={'comment_column': 'Comment', 'sentiment_column': 'Sentiment'})
except FileNotFoundError:
    print("❌ BŁĄD: Nie znaleziono pliku CSV. Zmień 'path/to/your/data.csv' na poprawną ścieżkę do danych.")
    print(path)
    exit()

sentiment_mapping = {
    'negative': 0,
    'neutral': 1,
    'positive': 2
}
df['Sentiment'] = df['Sentiment'].map(sentiment_mapping)

print("--- Przygotowanie danych zakończone ---")
print("--- Trenowanie... ---")



# ----------------------------------------------------------------------
# 2. DEFINICJA FUNKCJI TRENINGOWEJ
# ----------------------------------------------------------------------

def split_and_vectorize_text(X, y, test_size=0.2):
    # 🎯 Używamy zaimportowanej funkcji 'text_tokenizer'
    vectorizer = TfidfVectorizer(
        tokenizer=text_tokenizer,  # Wektoryzator używa funkcji z data_processing.preprocessing_text
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.9
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    X_train_transform = vectorizer.fit_transform(X_train)
    X_test_transform = vectorizer.transform(X_test)
    print(f'Wielkość danych po przetworzeniu: {X_train_transform.shape}')

    return X_train_transform, X_test_transform, y_train, y_test, vectorizer


# ----------------------------------------------------------------------
# 3. URUCHOMIENIE I SERIALIZACJA (NOWY PLIK .joblib)
# ----------------------------------------------------------------------

# Uruchamiamy proces
X_train, X_test, y_train, y_test, fitted_vectorizer = split_and_vectorize_text(df['Comment'], df['Sentiment'],
                                                                               test_size=0.2)

# Ustalenie ścieżki do folderu Django
# Zakładając, że uruchamiasz to z katalogu głównego projektu:
MODEL_DIR = os.path.join(os.getcwd(),  'colab_train_models', 'models')

# Utwórz folder, jeśli nie istnieje
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

vectorizer_path = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')

# Zapisanie wytrenowanego wektoryzatora
joblib.dump(fitted_vectorizer, vectorizer_path)

print(f"\n✅ NOWY Wektoryzator został zapisany do: {vectorizer_path}")
print("Możesz teraz usunąć wklejony kod preprocessingowy z data_processing/views.py i przywrócić import.")
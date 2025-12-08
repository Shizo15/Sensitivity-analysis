# train_and_serialize.py
import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import ComplementNB
from sklearn.metrics import classification_report

from data_processing.preprocessing_text import text_tokenizer

# ----------------------------------------------------------------------
# 1. LOADING AND PREPARING DATA
# ----------------------------------------------------------------------

path = '../colab_train_models/Data/1_training_data_high_quality.csv'
try:
    df = pd.read_csv(path)
except FileNotFoundError:
    print(f"❌ ERROR: CSV file not found at path: {path}")
    print("Check if you are running the script from the main project directory.")
    exit()

# Sentiment mapping
sentiment_mapping = {
    'negative': 0,
    'neutral': 1,
    'positive': 2
}
df['Sentiment'] = df['Sentiment'].map(sentiment_mapping)
df.dropna(subset=['Sentiment', 'Comment'], inplace=True)  # Dropping NaN values

print(f"--- Data preparation complete. Number of samples: {len(df)} ---")
print("--- Starting training and vectorization... ---")


# ----------------------------------------------------------------------
# 2. VECTORIZATION AND SPLITTING FUNCTION
# ----------------------------------------------------------------------

def split_and_vectorize_text(X, y, test_size=0.2):
    vectorizer = TfidfVectorizer(
        tokenizer=text_tokenizer,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.9
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    X_train_transform = vectorizer.fit_transform(X_train)
    X_test_transform = vectorizer.transform(X_test)

    print(f'Data size after processing: {X_train_transform.shape}')

    return X_train_transform, X_test_transform, y_train, y_test, vectorizer


# ----------------------------------------------------------------------
# 3. VECTORIZATION and SERIALIZATION SETTINGS
# ----------------------------------------------------------------------

X_train, X_test, y_train, y_test, fitted_vectorizer = split_and_vectorize_text(df['Comment'], df['Sentiment'], test_size=0.2)

# Directory to save models
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'colab_train_models', 'models')

# Ensuring the folder exists
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)
    print(f"Created target folder: {MODEL_DIR}")

# ----------------------------------------------------------------------
# 4. TRAINING AND SAVING THE VECTORIZER
# ----------------------------------------------------------------------

vectorizer_path = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')
joblib.dump(fitted_vectorizer, vectorizer_path)
print(f"\n✅ Saved TF-IDF Vectorizer to: {vectorizer_path}")

# ----------------------------------------------------------------------
# 5. TRAINING AND SAVING CLASSIFICATION MODELS
# ----------------------------------------------------------------------

MODELS_TO_TRAIN = {
    'logistic_regression': (LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000), 'logistic_regression_model.joblib'),
    'naive_bayes': (ComplementNB(), 'naive_model.joblib'),
    'svc': (SVC(kernel='linear', class_weight='balanced', random_state=42), 'svc_model.joblib')
}

print("\n--- Starting training of classification models ---")

for model_name, (classifier, file_name) in MODELS_TO_TRAIN.items():
    print(f"\n⏳ Training model: {model_name}...")

    try:
        classifier.fit(X_train, y_train)
        y_pred = classifier.predict(X_test)

        # Saving the model
        model_path = os.path.join(MODEL_DIR, file_name)
        joblib.dump(classifier, model_path)

        print(f"✅ Saved model '{model_name}' to: {model_path}")
        print(f"Report on the test set:\n{classification_report(y_test, y_pred)}")

    except Exception as e:
        print(f"❌ ERROR during training/saving model {model_name}: {e}")

print("\n=======================================================")
print("✅ Training and serialization process COMPLETED SUCCESSFULLY.")
print("You can now run the Django server: python manage.py runserver")
print("=======================================================")
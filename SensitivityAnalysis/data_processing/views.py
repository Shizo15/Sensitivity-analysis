from django.contrib import messages
from django.shortcuts import render, redirect
import os
import joblib
from django.shortcuts import render
from django.conf import settings
from django.views import View

# 1. IMPORT loading yt comments
from youtube_integration.services import get_yt_comments, get_yt_video_meta


# ---------preprocessing  ----------
# StopWords
from spacy.lang.en.stop_words import STOP_WORDS
import re
import spacy

stopwords_set = set(STOP_WORDS)
exclude_words = {'no', 'not', 'never', 'neither', 'nor', 'none', 'cannot'} # Words to keep
final_stopwords = list(stopwords_set - exclude_words)


def clean_text(text):
    text = str(text)
    temp = text.lower()
    #temp = re.sub(r'\d+', '', temp)
    temp = re.sub(r'<[^>]*>', '', temp)
    emojis = re.findall(r'(?::|;|=)(?:-)?(?:\)|\(|D|P)', temp)
    temp = re.sub(r'[^a-zA-Z\s]', ' ', temp)
    temp = temp + ' ' + ' '.join(emojis).replace('-', '')
    temp = re.sub(r'\s+', ' ', temp).strip()

    return temp

# Lemantization with spaCy:
try:
    nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])
except OSError:
    print("Downloading spaCy (en_core_web_sm)...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])

def text_tokenizer(text):
    cleaned_text = clean_text(text)

    doc = nlp(cleaned_text)

    # (e.g., "was" -> "be", "dogs" -> "dog")
    lemmas = [token.lemma_ for token in doc]

    # Filtering
    return [lemma for lemma in lemmas if lemma not in final_stopwords and len(lemma) > 2]


# --- LOAD MODELS ---
# location of saved models
MODEL_DIR = os.path.join(settings.BASE_DIR, 'data_processing', 'colab_train_models', 'models')

try:
    # Load the TF-IDF Vectorizer
    VECTORIZER = joblib.load(os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib'))

    # load model
    logistic_regression_model = joblib.load(os.path.join(MODEL_DIR, 'logistic_regression_model.joblib'))
    naive_bayes_model = joblib.load(os.path.join(MODEL_DIR, 'naive_model.joblib'))
    svc_model = joblib.load(os.path.join(MODEL_DIR, 'svc_model.joblib'))

    MODEL_CATALOG = {
        'logistic_regression': logistic_regression_model,
        'naive_bayes': naive_bayes_model,
        'svc': svc_model,
    }

    print("Models loaded successfully.")

except Exception as e:
    VECTORIZER = None
    MODEL_CATALOG = {'no_models': None,}
    print(f"Error by loading models: {e}")


# --- run model ---
def run_analysis(request):
    """
    Load video_id i model_name from sesji, and makes ML analysis,
    and redirect to results_dashboard with results saved in session.
    """
    #
    params = request.session.pop('analysis_params', None)

    if not params:
        messages.error(request, "No params found for analysis.")
        return redirect('sentiment_dashboard')

    video_id = params['video_id']
    model_name = params['model_name']

    # Map model names to loaded models
    CLASSIFIER = MODEL_CATALOG.get(model_name)

    if CLASSIFIER is None or VECTORIZER is None:
        messages.error(request, f"Error: Model '{model_name}' or vector isn't loaded.")
        return redirect('sentiment_dashboard')


    try:
        # loading comments and video meta from get YT API
        comments_list = get_yt_comments(video_id, max_results_total=500)
        title, thumb, channel, published_at, views, likes = get_yt_video_meta(video_id)

        # Preprocess comments
        processed_comments = []
        for comment in comments_list:
            tokens = text_tokenizer(comment)
            processed_comments.append(" ".join(tokens))

        # Vectorize comments and predict sentiments
        comments_vectorized = VECTORIZER.transform(processed_comments)
        predictions = CLASSIFIER.predict(comments_vectorized)

        # Calculate sentiment counts (e.g., positive, negative, neutral)
        sentiment_counts = {}
        for pred in predictions:
            key = int(pred)
            sentiment_counts[key] = sentiment_counts.get(key, 0) + 1

        # TODO add more statistics if needed

        # Save results in session
        request.session['last_stats'] = {
            'comment_count': len(comments_list),
            'video_title': title,
            'thumbnail_url': thumb,
            'channel_title': channel,
            'sentiment_counts': sentiment_counts,
            'model_used': model_name,
            # ... other statistics ...
        }

        # Redirect to results dashboard
        return redirect('results_dashboard')

    except Exception as e:
        messages.error(request, f"Error in data analysis: {e}")
        return redirect('sentiment_dashboard')
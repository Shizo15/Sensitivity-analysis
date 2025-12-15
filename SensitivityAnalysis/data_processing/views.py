from django.contrib import messages
from django.http import JsonResponse
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

# deep models
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

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
ROBERTA_MODEL_DIR = os.path.join(settings.BASE_DIR, 'data_processing', 'colab_train_models', 'models', 'roberta_model')

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
    # Loading RoBERTa model
    if os.path.exists(ROBERTA_MODEL_DIR):
        print("Loading RoBERTa model...")
        # Loading tokenizer
        TOKENIZER_ROBERTA = AutoTokenizer.from_pretrained(ROBERTA_MODEL_DIR)
        model_roberta = AutoModelForSequenceClassification.from_pretrained(ROBERTA_MODEL_DIR)

        #Switching to evaluation mode
        model_roberta.eval()

        MODEL_CATALOG['roberta'] = model_roberta
        print("RoBERTa loaded successfully.")
    else:
        print(f"Warning: RoBERTa directory not found at {ROBERTA_MODEL_DIR}")

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

        predictions = []

        # Deep model
        if model_name == 'roberta':
            for comment in comments_list:
                # Tokenization
                inputs = TOKENIZER_ROBERTA(
                    comment,
                    return_tensors="pt",
                    truncation=True,
                    max_length=128,
                    padding=True
                )

                # Prediction
                with torch.no_grad():
                    outputs = CLASSIFIER(**inputs)

                probs = F.softmax(outputs.logits, dim=-1)
                pred_label = torch.argmax(probs, dim=-1).item()

                final_pred = pred_label - 1
                predictions.append(final_pred)

        # Shallow models
        else:
            if VECTORIZER is None:
                raise ValueError("Vectorizer not loaded for shallow models")

            # 1. Preprocessing (lematization, stop words removal)
            processed_comments = []
            for comment in comments_list:
                tokens = text_tokenizer(comment)
                processed_comments.append(" ".join(tokens))

            # 2. Vectorization
            comments_vectorized = VECTORIZER.transform(processed_comments)

            # 3. Prediction
            predictions = CLASSIFIER.predict(comments_vectorized)

        idx_to_label = {
            0: 'negative',
            1: 'neutral',
            2: 'positive',
        }

        classified_comments = []
        for text, pred in zip(comments_list, predictions):
            p = int(pred)
            label = idx_to_label.get(p, 'unknown')
            classified_comments.append({
                'text': text,
                'label': label
            })

        # Calculate sentiment counts (0 = negative, 1 = neutral, 2 = positive)
        sentiment_counts = {}
        for pred in predictions:
            key = int(pred)
            sentiment_counts[key] = sentiment_counts.get(key, 0) + 1

        for k in [0, 1, 2]:
            sentiment_counts.setdefault(k, 0)

        total = sum(sentiment_counts.values()) or 1

        idx_to_label = {
            0: 'negative',
            1: 'neutral',
            2: 'positive',
        }

        sentiment_share = {
            idx_to_label[k]: round((count / total) * 100.0, 1)
            for k, count in sentiment_counts.items()
        }

        if len(predictions) > 0:
            old_avg = float(sum(predictions) / len(predictions))  # 0 to 2
            avg_sentiment_score = round(old_avg - 1, 2)  # -1 to +1
            avg_sentiment_percent = round(((avg_sentiment_score + 1) / 2) * 100, 1)

        else:
            avg_sentiment_score = None
            avg_sentiment_percent = None

        dominant_class = max(sentiment_counts, key=sentiment_counts.get) if total > 0 else None
        if dominant_class is not None:
            dominant_sentiment = idx_to_label[dominant_class]
            dominant_sentiment_percent = round(
                (sentiment_counts[dominant_class] / total) * 100.0, 1
            )
        else:
            dominant_sentiment = None
            dominant_sentiment_percent = None

        # Save results in session
        request.session['last_stats'] = {
            'comment_count': len(comments_list),
            'video_title': title,
            'thumbnail_url': thumb,
            'channel_title': channel,
            'published_at': published_at,
            'view_count': views,
            'like_count': likes,

            'sentiment_counts': sentiment_counts,
            'sentiment_share': sentiment_share,
            'avg_sentiment_score': avg_sentiment_score,
            'avg_sentiment_percent': avg_sentiment_percent,
            'dominant_sentiment': dominant_sentiment,
            'dominant_sentiment_percent': dominant_sentiment_percent,
            'model_used': model_name,
            'classified_comments': classified_comments,

        }

        return JsonResponse({"status": "done"})

    except Exception as e:
        messages.error(request, f"Error in data analysis: {e}")
        return redirect('sentiment_dashboard')
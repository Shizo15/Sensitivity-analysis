from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
import os
import joblib
import time
from django.conf import settings
# 1. IMPORT loading yt comments
from youtube_integration.services import get_yt_comments, get_yt_video_meta, PRO_COMMENT_LIMIT


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
exclude_words = {'no', 'not', 'never', 'neither', 'nor', 'none', 'cannot'}
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
    MODEL_CATALOG = {
        'logistic_regression': joblib.load(os.path.join(MODEL_DIR, 'logistic_regression_model.joblib')),
        'naive_bayes': joblib.load(os.path.join(MODEL_DIR, 'naive_model.joblib')),
        'svc': joblib.load(os.path.join(MODEL_DIR, 'svc_model.joblib')),
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


# NEW STATUS FUNCTION
def get_analysis_status(request):
    return JsonResponse(request.session.get('analysis_status', {'progress': 0, 'step': 'Waiting...'}))


def run_analysis(request):
    print("\n--- STARTING ANALYSIS (views.py) ---")
    start_total = time.time()
    params = request.session.pop('analysis_params', None)
    if not params: return redirect('sentiment_dashboard')

    video_id, model_name = params['video_id'], params['model_name']
    CLASSIFIER = MODEL_CATALOG.get(model_name)

    def update_step(progress, step_name):
        request.session['analysis_status'] = {'progress': progress, 'step': step_name}
        request.session.save()

    try:
        # STEP 1
        update_step(10, "Downloading comments from YouTube...")
        comments_list = get_yt_comments(video_id)
        title, thumb, channel, published_at, views, likes = get_yt_video_meta(video_id)

        predictions = []
        # STEP 2
        if model_name == 'roberta':
            update_step(40, "Analyzing RoBERTa model (Deep Learning)...")
            s_time = time.time()
            for comment in comments_list:
                inputs = TOKENIZER_ROBERTA(comment, return_tensors="pt", truncation=True, max_length=128, padding=True)
                with torch.no_grad(): outputs = CLASSIFIER(**inputs)
                predictions.append(torch.argmax(F.softmax(outputs.logits, dim=-1), dim=-1).item())
            print(f"RoBERTa classification: {time.time() - s_time:.2f} s")
        else:
            update_step(30, "Processing text and filtering...")
            s_time = time.time()
            processed = [" ".join(text_tokenizer(c)) for c in comments_list]
            print(f"Preprocessing: {time.time() - s_time:.2f} s")

            update_step(70, f"Running model: {model_name}...")
            s_time = time.time()
            predictions = CLASSIFIER.predict(VECTORIZER.transform(processed))
            print(f"ML Classification: {time.time() - s_time:.2f} s")

        # STEP 3: CALCULATIONS
        update_step(90, "Calculating final results...")
        idx_to_label = {0: 'negative', 1: 'neutral', 2: 'positive'}
        classified_comments = [{'text': t, 'label': idx_to_label.get(int(p), 'unknown')} for t, p in
                               zip(comments_list, predictions)]

        sentiment_counts = {0: 0, 1: 0, 2: 0}
        for pred in predictions: sentiment_counts[int(pred)] = sentiment_counts.get(int(pred), 0) + 1

        total = len(predictions) or 1
        sentiment_share = {idx_to_label[k]: round((sentiment_counts[k] / total) * 100.0, 1) for k in [0, 1, 2]}

        if len(predictions) > 0:
            avg_score = round(float(sum(predictions) / len(predictions)) - 1, 2)
            avg_percent = round(((avg_score + 1) / 2) * 100, 1)
            dominant_class = max(sentiment_counts, key=sentiment_counts.get)
            dominant_sentiment = idx_to_label[dominant_class]
            dominant_percent = round((sentiment_counts[dominant_class] / total) * 100.0, 1)
        else:
            avg_score = avg_percent = 0
            dominant_sentiment = "N/A"
            dominant_percent = 0

        request.session['last_stats'] = {
            'comment_count': len(comments_list), 'video_title': title, 'thumbnail_url': thumb,
            'channel_title': channel, 'published_at': published_at, 'view_count': views, 'like_count': likes,
            'sentiment_counts': sentiment_counts, 'sentiment_share': sentiment_share,
            'avg_sentiment_score': avg_score, 'avg_sentiment_percent': avg_percent,
            'dominant_sentiment': dominant_sentiment, 'dominant_sentiment_percent': dominant_percent,
            'model_used': model_name, 'classified_comments': classified_comments,
        }

        print(f"--- ANALYSIS FINISHED: {time.time() - start_total:.2f} s ---\n")
        update_step(100, "Done!")
        return JsonResponse({"status": "done"})
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"status": "error", "message": str(e)})
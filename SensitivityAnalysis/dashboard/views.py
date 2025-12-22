from django.shortcuts import render, redirect
from django.contrib import messages
import re

from data_processing.views import MODEL_CATALOG
import json
# check video limit
from youtube_integration.services import check_video_limit

DISPLAY_NAMES = {
    'logistic_regression': 'Regresja Logistyczna',
    'svc': 'Support Vector Machine (SVC)',
    'naive_bayes': 'Klasyfikator Naiwnego Bayesa',
}

def extract_video_id(link):
    if not link:
        return None

    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    match = re.search(youtube_regex, link)
    if not match:
        return None

    return match.group(6)


def sentiment_dashboard(request):
    """
    Main view to submit YouTube link and select model for sentiment analysis.
    Handles form submission, validates input, checks comment limits,
    and redirects to loading page for analysis.
    1. GET: Renders the main form.
    2. POST: Processes the submitted form.
    3. On success, saves parameters in session and redirects to 'loading' view.
    4. On error, displays appropriate messages.
    """
    submitted_link = ""

    if request.method == 'POST':
        submitted_link = request.POST.get("youtube_link", "").strip()
        video_id = extract_video_id(submitted_link)
        model_name = request.POST.get("model_name", "logistic_regression")

        if not video_id:
            messages.error(request, "Input valid YouTube link.")
        else:
            # Check comment limit before proceeding, when 10000 comments exceeded, show error.
            is_allowed, limit_msg = check_video_limit(video_id)

            if not is_allowed:
                # loading and showing pro modal

                model_choices_for_template = [
                    (key, DISPLAY_NAMES.get(key, key.replace('_', ' ').title()))
                    for key in MODEL_CATALOG.keys()
                ]
                if 'roberta' not in MODEL_CATALOG:
                    model_choices_for_template.append(('roberta', 'RoBERTa (Deep Learning)'))

                context = {
                    'submitted_link': submitted_link,
                    'model_choices': model_choices_for_template,
                    'show_pro_modal': True,
                    'pro_modal_message': limit_msg
                }
                # rendering main.html with pro modal
                return render(request, "main.html", context)

            else:
                # if ok to proceed, go to loading page
                if model_name not in MODEL_CATALOG and model_name != 'roberta':
                    messages.error(request, f"Wybrany model ({model_name}) jest niedostępny.")
                    return redirect('sentiment_dashboard')

                request.session['analysis_params'] = {
                    'video_id': video_id,
                    'model_name': model_name
                }
                return redirect('loading')

    # GET request
    model_choices_for_template = [
        (key, DISPLAY_NAMES.get(key, key.replace('_', ' ').title()))
        for key in MODEL_CATALOG.keys()
    ]
    if 'roberta' not in MODEL_CATALOG:
        model_choices_for_template.append(('roberta', 'RoBERTa (Deep Learning)'))

    context = {
        'submitted_link': submitted_link,
        'model_choices': model_choices_for_template,
    }

    return render(request, "main.html", context)

def loading_view(request):
    return render(request, "loading.html")

def results_dashboard(request):
    data = request.session.get('last_stats', {})

    sentiment_share = data.get('sentiment_share') or {}

    context = {
        'comment_count': data.get('comment_count'),
        'video_title': data.get('video_title'),
        'thumbnail_url': data.get('thumbnail_url'),
        'channel_title': data.get('channel_title'),
        'published_at': data.get('published_at'),
        'view_count': data.get('view_count'),
        'like_count': data.get('like_count'),

        'sentiment_share': sentiment_share,
        'sentiment_share_json': json.dumps(sentiment_share),

        'avg_sentiment_score': data.get('avg_sentiment_score'),
        'avg_sentiment_percent': data.get('avg_sentiment_percent'),
        'dominant_sentiment': data.get('dominant_sentiment'),
        'dominant_sentiment_percent': data.get('dominant_sentiment_percent'),
        'model_used': data.get('model_used'),
        'classified_comments': data.get('classified_comments', []),

    }
    return render(request, "dashboard.html", context)

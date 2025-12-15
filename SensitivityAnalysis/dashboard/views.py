from django.shortcuts import render, redirect
from django.contrib import messages
from youtube_integration.services import get_yt_comments
import re
from youtube_integration.services import get_yt_comments, get_yt_video_meta

from data_processing.views import MODEL_CATALOG
import json

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
    Loads yt link and chose of model from form,
    saves params in session and redirect to run_analysis view.
    """

    submitted_link = ""

    if request.method == 'POST':
        submitted_link = request.POST.get("youtube_link", "").strip()
        video_id = extract_video_id(submitted_link)

        # load selected model from form
        model_name = request.POST.get("model_select", "logistic_regression")

        if not video_id:
            messages.error(request, "Input valid YouTube link.")
        else:
            # check if selected model is in catalog
            if model_name not in MODEL_CATALOG:
                messages.error(request, f"Chosen model ({model_name}) can't be used.")
                return redirect('loading')

            # save in session params for analysis
            request.session['analysis_params'] = {
                'video_id': video_id,
                'model_name': model_name
            }

            return redirect('loading')

        return redirect('loading')

    # GET request - load page if no form submitted

    # create list of model choices for template
    model_choices_for_template = [
        (key, DISPLAY_NAMES.get(key, key.replace('_', ' ').title()))
        for key in MODEL_CATALOG.keys()
    ]

    context = {
        'submitted_link': "",
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

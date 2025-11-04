from django.shortcuts import render
from django.contrib import messages

from youtube_integration.services import get_yt_comments

import re

#Extracting video id from link
def extract_video_id(link):
    if not link:
        return None

    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')

    match = re.search(youtube_regex, link)

    if not match:
        return None

    return match.group(6)

def sentiment_dashboard(request):
    # Wyczyść stare komunikaty przed wyświetleniem nowych
    storage = messages.get_messages(request)
    storage.used = True

    comments_list = None

    submitted_link = ""

    if request.method == 'POST':
        submitted_link = request.POST.get("youtube_link", "").strip()

        video_id = extract_video_id(submitted_link)

        if not video_id:
            messages.error(request, "Please enter a valid YouTube link.")

        else:
            try:
                comments_list = get_yt_comments(video_id, max_results_total=500)

                messages.success(request, f"Pobrano {len(comments_list)} komentarzy.")

                messages.info(request, f"Przykładowy komentarz: {comments_list[0]}")

                #TODO: Passing 'comments_list' to 'data_processing'

            except Exception as e:
                messages.error(request, f"Wystąpił nieprzewidziany błąd: {e}")

    context = {
        'comments': comments_list,
        'submitted_link': submitted_link, #link doesn't disappear after pressing 'Analyze' button
    }

    return render(request, "main.html", context)
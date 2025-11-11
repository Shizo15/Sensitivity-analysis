from django.shortcuts import render, redirect
from django.contrib import messages
from youtube_integration.services import get_yt_comments
import re

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
                messages.success(request, f"Downloaded {len(comments_list)} comments.")
                messages.info(request, f"Example comment: {comments_list[0]}")
            except Exception as e:
                messages.error(request, f"Unexpected error: {e}")

        # PRG: Redirect back to the same page to clear POST data
        return redirect('sentiment_dashboard')

    # GET request — just render a clean page
    context = {
        'comments': comments_list,
        'submitted_link': "",
    }

    return render(request, "main.html", context)
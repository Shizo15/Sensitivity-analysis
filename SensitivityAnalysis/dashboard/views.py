from django.shortcuts import render
from django.contrib import messages

# Create your views here.




def sentiment_dashboard(request):
    # Wyczyść stare komunikaty przed wyświetleniem nowych
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == "POST":
        youtube_link = request.POST.get("youtube_link")

        if not youtube_link.startswith(("https://www.youtube.com/", "https://youtu.be/")):
            messages.error(request, "Please enter a valid YouTube link.")
            return render(request, "main.html")

        messages.success(request, "Valid YouTube link! (analysis coming soon)")

    return render(request, "main.html")

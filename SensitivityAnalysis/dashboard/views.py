from django.shortcuts import render

# Create your views here.


def main(request):
    nazwa = "anna"
    return render(request, "main.html", {
        "nazwa": nazwa
    })
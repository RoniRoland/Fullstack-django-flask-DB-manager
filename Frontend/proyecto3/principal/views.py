from django.shortcuts import render


# Create your views here.
def home(request):
    return render(request, "home.html")


def carga(request):
    return render(request, "carga.html")

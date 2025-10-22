from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse("Hello my ama!")

def healthz(request):
    return HttpResponse("ok")
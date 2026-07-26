from django.shortcuts import render, get_object_or_404
from .models import Worker

def home(request):
    workers = Worker.objects.filter(available=True)
    return render(request, "home.html", {"workers": workers})


def worker_detail(request, worker_id):
    worker = get_object_or_404(Worker, id=worker_id)
    return render(request, "worker_detail.html", {"worker": worker})
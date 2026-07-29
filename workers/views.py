from django.shortcuts import render, get_object_or_404
from .models import Worker
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import WorkerRegistrationForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def worker_dashboard(request):
    worker = request.user.worker_profile

    return render(
        request,
        "worker_dashboard.html",
        {
            "worker": worker
        }
    )

def home(request):
    workers = Worker.objects.filter(available=True)
    return render(request, "home.html", {"workers": workers})


def worker_detail(request, worker_id):

    worker = get_object_or_404(Worker, id=worker_id)

    is_worker = False

    if request.user.is_authenticated:
        is_worker = hasattr(request.user, "worker_profile")

    print("User:", request.user.username if request.user.is_authenticated else "Guest")
    print("is_worker:", is_worker)

    return render(
        request,
        "worker_detail.html",
        {
            "worker": worker,
            "is_worker": is_worker,
        }
    )

def worker_register(request):

    if request.method == "POST":

        form = WorkerRegistrationForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            if User.objects.filter(username=username).exists():

                messages.error(
                    request,
                    "Username already exists."
                )

            else:

                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=form.cleaned_data["name"],
                )

                worker = form.save(commit=False)

                worker.user = user

                worker.save()

                messages.success(
                    request,
                    "Registration Successful. Please Login."
                )

                return redirect("login")

    else:

        form = WorkerRegistrationForm()

    return render(
        request,
        "worker_register.html",
        {
            "form": form
        }
    )


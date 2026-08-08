from django.shortcuts import render, get_object_or_404
from .models import Worker
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import WorkerRegistrationForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from bookings.models import Booking


@login_required
def worker_dashboard(request):

    worker = request.user.worker_profile

    bookings = Booking.objects.filter(
        worker=worker
    ).order_by("-created_at")

    total_bookings = bookings.count()

    pending_bookings = bookings.filter(
        status="Pending"
    ).count()

    accepted_bookings = bookings.filter(
        status="Accepted"
    ).count()

    completed_bookings = bookings.filter(
        status="Completed"
    ).count()

    return render(
        request,
        "worker_dashboard.html",
        {
            "worker": worker,
            "bookings": bookings,

            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "accepted_bookings": accepted_bookings,
            "completed_bookings": completed_bookings,
        }
    )

@login_required
def toggle_availability(request):

    worker = request.user.worker_profile

    worker.available = not worker.available
    worker.save()

    return redirect("worker_dashboard")

def home(request):
    workers = Worker.objects.filter(available=True)
    return render(request, "home.html", {"workers": workers})

def workers_by_profession(request, profession):

    workers = Worker.objects.filter(
        profession=profession,
        available=True
    )

    return render(
        request,
        "workers_list.html",
        {
            "workers": workers,
            "profession": profession,
        },
    )

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
@login_required
def update_booking_status(request, booking_id, status):

    worker = request.user.worker_profile

    booking = Booking.objects.get(
        id=booking_id,
        worker=worker
    )

    if status == "accept":

        booking.status = "Accepted"

    elif status == "reject":

        booking.status = "Cancelled"

    elif status == "complete":

        # Safety check: sirf accepted booking hi complete ho sakti hai
        if booking.status == "Accepted":
            booking.status = "Completed"

    booking.save()

    return redirect("worker_dashboard")
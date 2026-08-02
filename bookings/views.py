from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from workers.models import Worker
from .forms import BookingForm


@login_required
def book_worker(request, worker_id):

    worker = get_object_or_404(Worker, id=worker_id)
    print("Logged in user:", request.user.username)
    print("Is Worker:", hasattr(request.user, "worker_profile"))

    # Worker cannot book another worker
    if hasattr(request.user, "worker_profile"):

        messages.error(
            request,
            "Only customers can book workers."
        )

        return redirect("worker_detail", worker_id=worker.id)

    if request.method == "POST":

        form = BookingForm(request.POST)

        if form.is_valid():

            booking = form.save(commit=False)

            booking.worker = worker
            booking.customer = request.user

            # Auto-fill customer details
            booking.customer_name = (
                request.user.get_full_name()
                or request.user.first_name
                or request.user.username
            )

            # Mobile customer profile se aayega
            booking.customer_mobile = ""

            booking.save()

            return redirect("booking_success", booking.id)

    else:

        form = BookingForm()

    return render(
        request,
        "booking_form.html",
        {
            "form": form,
            "worker": worker
        }
    )

from .models import Booking

def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    return render(
        request,
        "booking_success.html",
        {
            "booking": booking
        }
    )
from django.shortcuts import render, redirect, get_object_or_404

from workers.models import Worker

from .forms import BookingForm

from django.contrib.auth.decorators import login_required

@login_required
def book_worker(request, worker_id):

    worker = get_object_or_404(Worker, id=worker_id)

    if request.method == "POST":

        form = BookingForm(request.POST)

        if form.is_valid():

            booking = form.save(commit=False)

            booking.worker = worker

            booking.customer = request.user

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
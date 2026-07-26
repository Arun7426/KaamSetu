from django.shortcuts import render, redirect, get_object_or_404

from workers.models import Worker

from .forms import BookingForm


def book_worker(request, worker_id):

    worker = get_object_or_404(Worker, id=worker_id)

    if request.method == "POST":

        form = BookingForm(request.POST)

        if form.is_valid():

            booking = form.save(commit=False)

            booking.worker = worker

            booking.save()

            return redirect("home")

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
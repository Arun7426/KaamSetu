from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from workers.models import Worker
from accounts.models import CustomerProfile
from .forms import BookingForm
from django.db.models import Avg
from .models import Booking, Review
from .forms import BookingForm, ReviewForm

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

            # Auto-fill customer name
            booking.customer_name = (
                request.user.get_full_name()
                or request.user.first_name
                or request.user.username
            )

            # Auto-fill customer mobile
            try:
                booking.customer_mobile = request.user.customer_profile.mobile
            except CustomerProfile.DoesNotExist:
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


@login_required
def booking_success(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    return render(
        request,
        "booking_success.html",
        {
            "booking": booking
        }
    )

@login_required
def add_review(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user
    )

    # Review only after completed work
    if booking.status != "Completed":
        messages.error(
            request,
            "You can review only after the work is completed."
        )
        return redirect("customer_dashboard")

    # Prevent duplicate review
    if hasattr(booking, "review"):
        messages.warning(
            request,
            "You have already reviewed this booking."
        )
        return redirect("customer_dashboard")

    if request.method == "POST":

        form = ReviewForm(request.POST)

        if form.is_valid():

            review = form.save(commit=False)

            review.booking = booking
            review.worker = booking.worker
            review.customer = request.user

            review.save()

            # ---------- Update Worker Rating ----------
            worker = booking.worker

            avg_rating = worker.worker_reviews.aggregate(
                Avg("rating")
            )["rating__avg"]

            worker.rating = round(avg_rating, 1)
            worker.reviews = worker.worker_reviews.count()

            worker.save()

            messages.success(
                request,
                "Thank you! Your review has been submitted."
            )

            return redirect("customer_dashboard")

    else:

        form = ReviewForm()

    return render(
        request,
        "review_form.html",
        {
            "form": form,
            "booking": booking,
        }
    )
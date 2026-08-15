from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Avg

from workers.models import Worker
from accounts.models import CustomerProfile

from .forms import BookingForm, ReviewForm
from .models import Booking, Review


# =========================================================
# BOOK WORKER
# =========================================================

@login_required
def book_worker(request, worker_id):

    worker = get_object_or_404(Worker, id=worker_id)

    # Worker cannot book another worker
    if hasattr(request.user, "worker_profile"):

        messages.error(
            request,
            "Only customers can book workers."
        )

        return redirect(
            "worker_detail",
            worker_id=worker.id
        )

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
                booking.customer_mobile = (
                    request.user.customer_profile.mobile
                )

            except CustomerProfile.DoesNotExist:
                booking.customer_mobile = ""

            # -----------------------------------------
            # Save worker's current wage as booking
            # original amount
            # -----------------------------------------
            booking.original_amount = int(worker.daily_wage)

            booking.save()

            return redirect(
                "booking_success",
                booking.id
            )

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


# =========================================================
# BOOKING SUCCESS
# =========================================================

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


# =========================================================
# NEGOTIATION - SUGGESTED AMOUNTS
# =========================================================

def get_customer_offer_suggestions(original_amount):
    """
    Customer suggestions:
    Original amount - 300
    Original amount - 200
    Original amount - 100

    Valid range:
    ₹1 to ₹9,999
    """

    suggestions = [
        original_amount - 300,
        original_amount - 200,
        original_amount - 100,
    ]

    # Remove invalid amounts and duplicates
    suggestions = sorted(
        set(
            amount
            for amount in suggestions
            if 1 <= amount <= 9999
        )
    )

    return suggestions


def get_worker_counter_suggestions(customer_offer):
    """
    Worker counter suggestions:
    Customer offer + 100
    Customer offer + 200
    Customer offer + 300

    Valid range:
    ₹1 to ₹9,999
    """

    suggestions = [
        customer_offer + 100,
        customer_offer + 200,
        customer_offer + 300,
    ]

    # Remove invalid amounts and duplicates
    suggestions = sorted(
        set(
            amount
            for amount in suggestions
            if 1 <= amount <= 9999
        )
    )

    return suggestions


# =========================================================
# CUSTOMER - MAKE OFFER
# =========================================================

@login_required
def customer_make_offer(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user
    )

    # Negotiation is available only after worker accepts
    if booking.status != "Accepted":

        messages.error(
            request,
            "Negotiation is available only after the worker accepts the booking."
        )

        return redirect("customer_dashboard")

    # Negotiation can only start once
    if booking.negotiation_status != "Not Started":

        messages.warning(
            request,
            "Negotiation has already started for this booking."
        )

        return redirect("customer_dashboard")

    # Old booking without original amount
    if booking.original_amount is None:

        messages.error(
            request,
            "Original booking amount is not available for negotiation."
        )

        return redirect("customer_dashboard")

    suggestions = get_customer_offer_suggestions(
        booking.original_amount
    )

    if request.method == "POST":

        try:
            offer = int(request.POST.get("offer_amount", ""))

        except (TypeError, ValueError):

            messages.error(
                request,
                "Please select a valid offer amount."
            )

            return redirect(
                "customer_make_offer",
                booking_id=booking.id
            )

        # Only suggested amounts are allowed
        if offer not in suggestions:

            messages.error(
                request,
                "Please select one of the suggested offer amounts."
            )

            return redirect(
                "customer_make_offer",
                booking_id=booking.id
            )

        booking.customer_offer = offer
        booking.negotiation_status = "Customer Offered"

        booking.save(
            update_fields=[
                "customer_offer",
                "negotiation_status"
            ]
        )

        messages.success(
            request,
            f"Your offer of ₹{offer} has been sent to the worker."
        )

        return redirect("customer_dashboard")

    return render(
        request,
        "customer_make_offer.html",
        {
            "booking": booking,
            "suggestions": suggestions,
        }
    )


# =========================================================
# WORKER - RESPOND TO CUSTOMER OFFER
# =========================================================

@login_required
def worker_respond_offer(request, booking_id):

    worker = request.user.worker_profile

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        worker=worker
    )

    # Worker can respond only to customer's active offer
    if booking.negotiation_status != "Customer Offered":

        messages.error(
            request,
            "There is no active customer offer for this booking."
        )

        return redirect("worker_dashboard")

    if booking.customer_offer is None:

        messages.error(
            request,
            "Customer offer is not available."
        )

        return redirect("worker_dashboard")

    suggestions = get_worker_counter_suggestions(
        booking.customer_offer
    )

    if request.method == "POST":

        action = request.POST.get("action")

        # -----------------------------------------
        # Worker accepts customer's offer
        # -----------------------------------------
        if action == "accept":

            booking.final_amount = booking.customer_offer
            booking.negotiation_status = "Accepted"

            booking.save(
                update_fields=[
                    "final_amount",
                    "negotiation_status"
                ]
            )

            messages.success(
                request,
                f"Customer's offer of ₹{booking.final_amount} has been accepted."
            )

            return redirect("worker_dashboard")

        # -----------------------------------------
        # Worker sends counter offer
        # -----------------------------------------
        elif action == "counter":

            try:
                counter_offer = int(
                    request.POST.get("counter_amount", "")
                )

            except (TypeError, ValueError):

                messages.error(
                    request,
                    "Please select a valid counter offer."
                )

                return redirect(
                    "worker_respond_offer",
                    booking_id=booking.id
                )

            # Only suggested counter amounts are allowed
            if counter_offer not in suggestions:

                messages.error(
                    request,
                    "Please select one of the suggested counter offer amounts."
                )

                return redirect(
                    "worker_respond_offer",
                    booking_id=booking.id
                )

            booking.worker_counter_offer = counter_offer
            booking.negotiation_status = "Worker Countered"

            booking.save(
                update_fields=[
                    "worker_counter_offer",
                    "negotiation_status"
                ]
            )

            messages.success(
                request,
                f"Counter offer of ₹{counter_offer} has been sent to the customer."
            )

            return redirect("worker_dashboard")

    return render(
        request,
        "worker_respond_offer.html",
        {
            "booking": booking,
            "suggestions": suggestions,
        }
    )


# =========================================================
# CUSTOMER - ACCEPT / REJECT WORKER COUNTER OFFER
# =========================================================

@login_required
def customer_respond_counter(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user
    )

    # Customer can respond only to worker counter offer
    if booking.negotiation_status != "Worker Countered":

        messages.error(
            request,
            "There is no active counter offer for this booking."
        )

        return redirect("customer_dashboard")

    if booking.worker_counter_offer is None:

        messages.error(
            request,
            "Worker counter offer is not available."
        )

        return redirect("customer_dashboard")

    if request.method == "POST":

        action = request.POST.get("action")

        # -----------------------------------------
        # Customer accepts worker counter offer
        # -----------------------------------------
        if action == "accept":

            booking.final_amount = booking.worker_counter_offer
            booking.negotiation_status = "Accepted"

            booking.save(
                update_fields=[
                    "final_amount",
                    "negotiation_status"
                ]
            )

            messages.success(
                request,
                f"You accepted the worker's counter offer of ₹{booking.final_amount}."
            )

            return redirect("customer_dashboard")

        # -----------------------------------------
        # Customer rejects worker counter offer
        # -----------------------------------------
        elif action == "reject":

            booking.negotiation_status = "Rejected"
            booking.status = "Cancelled"

            booking.save(
                update_fields=[
                    "negotiation_status",
                    "status"
                ]
            )

            messages.success(
                request,
                "You rejected the counter offer. The booking has been cancelled."
            )

            return redirect("customer_dashboard")

    return render(
        request,
        "customer_respond_counter.html",
        {
            "booking": booking,
        }
    )


# =========================================================
# ADD REVIEW
# =========================================================

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

            # -----------------------------------------
            # Update Worker Rating
            # -----------------------------------------
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
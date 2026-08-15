from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from bookings.models import Booking
from bookings.notifications import create_notification

from .forms import WorkerRegistrationForm
from .location import nearby_workers
from .models import Worker


# Hindi service words → database profession names
SEARCH_ALIASES = {
    "पेंटर": "Painter",
    "प्लंबर": "Plumber",
    "प्लम्बर": "Plumber",
    "इलेक्ट्रीशियन": "Electrician",
    "बिजली मिस्त्री": "Electrician",
    "राजमिस्त्री": "Rajmistri",
    "राज मिस्त्री": "Rajmistri",
    "कारपेंटर": "Carpenter",
    "बढ़ई": "Carpenter",
}


@login_required
def worker_dashboard(request):
    worker = request.user.worker_profile

    bookings = Booking.objects.filter(
        worker=worker
    ).order_by("-created_at")

    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status="Pending").count()
    accepted_bookings = bookings.filter(status="Accepted").count()
    completed_bookings = bookings.filter(status="Completed").count()

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
    search_query = request.GET.get("q", "").strip()

    # Hindi service name को database profession में convert करें
    search_term = SEARCH_ALIASES.get(
        search_query.lower(),
        search_query
    )

    # अगर search किसी profession का है,
    # तो सीधे उस profession के workers वाले page पर जाएँ
    if search_term:
        profession_exists = Worker.objects.filter(
            profession__iexact=search_term
        ).exists()

        if profession_exists:
            return redirect(
                "workers_by_profession",
                profession=search_term
            )

    # Normal home page
    workers = Worker.objects.filter(available=True)

    # Existing customer location + worker work-range filtering
    workers, location_context = filter_workers_for_customer(
        request,
        workers
    )

    return render(
        request,
        "home.html",
        {
            "workers": workers,
            "search_query": search_query,
            **location_context,
        }
    )


def workers_by_profession(request, profession):
    workers = Worker.objects.filter(
        profession=profession,
        available=True
    )

    workers, location_context = filter_workers_for_customer(
        request,
        workers
    )

    return render(
        request,
        "workers_list.html",
        {
            "workers": workers,
            "profession": profession,
            **location_context,
        },
    )


def filter_workers_for_customer(request, workers):
    """Apply a worker's service radius when a customer has shared a location."""
    context = {
        "customer_location_required": False,
        "nearby_filter_active": False,
    }

    if not request.user.is_authenticated or hasattr(
        request.user,
        "worker_profile"
    ):
        return workers, context

    try:
        customer = request.user.customer_profile
    except ObjectDoesNotExist:
        return workers, context

    if customer.latitude is None or customer.longitude is None:
        context["customer_location_required"] = True
        return workers, context

    context["nearby_filter_active"] = True

    return nearby_workers(
        workers,
        (customer.latitude, customer.longitude)
    ), context


def worker_detail(request, worker_id):
    worker = get_object_or_404(Worker, id=worker_id)

    is_worker = False

    if request.user.is_authenticated:
        is_worker = hasattr(request.user, "worker_profile")

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


# =========================================================
# UPDATE BOOKING STATUS
# =========================================================

@login_required
def update_booking_status(request, booking_id, status):

    worker = request.user.worker_profile

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        worker=worker
    )

    # -----------------------------------------
    # ACCEPT BOOKING
    # -----------------------------------------

    if status == "accept":

        if booking.status != "Pending":

            messages.error(
                request,
                "This booking is no longer pending."
            )

            return redirect(
                "worker_dashboard"
            )

        booking.status = "Accepted"

        booking.save(
            update_fields=["status"]
        )

        # Notify customer
        create_notification(
            recipient=booking.customer,
            booking=booking,
            notification_type="accepted",
            message=(
                f"{worker.name} accepted your booking. "
                f"You can now make an offer."
            )
        )

        messages.success(
            request,
            "Booking accepted. Customer can now make an offer."
        )


    # -----------------------------------------
    # REJECT BOOKING
    # -----------------------------------------

    elif status == "reject":

        if booking.status != "Pending":

            messages.error(
                request,
                "This booking cannot be rejected now."
            )

            return redirect(
                "worker_dashboard"
            )

        booking.status = "Cancelled"

        booking.save(
            update_fields=["status"]
        )

        # Notify customer
        create_notification(
            recipient=booking.customer,
            booking=booking,
            notification_type="rejected",
            message=(
                f"{worker.name} rejected your booking request."
            )
        )

        messages.success(
            request,
            "Booking has been cancelled."
        )


    # -----------------------------------------
    # COMPLETE WORK
    # -----------------------------------------

    elif status == "complete":

        if booking.status != "Accepted":

            messages.error(
                request,
                "This booking is not active."
            )

            return redirect(
                "worker_dashboard"
            )

        if booking.negotiation_status != "Accepted":

            messages.error(
                request,
                "You can complete the work only after the negotiation is completed and the booking is finally confirmed."
            )

            return redirect(
                "worker_dashboard"
            )

        if booking.final_amount is None:

            messages.error(
                request,
                "Final amount is not available. The booking cannot be completed."
            )

            return redirect(
                "worker_dashboard"
            )

        booking.status = "Completed"

        booking.save(
            update_fields=["status"]
        )

        # Notify customer
        create_notification(
            recipient=booking.customer,
            booking=booking,
            notification_type="completed",
            message=(
                f"{worker.name} marked your work as completed."
            )
        )

        messages.success(
            request,
            "Work marked as completed successfully."
        )


    # -----------------------------------------
    # INVALID STATUS
    # -----------------------------------------

    else:

        messages.error(
            request,
            "Invalid booking status."
        )

        return redirect(
            "worker_dashboard"
        )

    return redirect(
        "worker_dashboard"
    )

@login_required
@require_POST
def update_worker_location(request):
    """Save the authenticated worker's browser-provided coordinates."""
    try:
        latitude = Decimal(request.POST.get("latitude", ""))
        longitude = Decimal(request.POST.get("longitude", ""))

    except (InvalidOperation, TypeError):
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid location coordinates received.",
            },
            status=400,
        )

    if (
        not latitude.is_finite()
        or not longitude.is_finite()
        or not (-90 <= latitude <= 90 and -180 <= longitude <= 180)
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "Location coordinates are outside the valid range.",
            },
            status=400,
        )

    try:
        worker = request.user.worker_profile

    except ObjectDoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Only workers can update this location.",
            },
            status=403,
        )

    worker.latitude = latitude
    worker.longitude = longitude
    worker.save(
        update_fields=[
            "latitude",
            "longitude"
        ]
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Your current location has been saved successfully.",
        }
    )


@login_required
@require_POST
def update_work_range(request):
    try:
        work_range = Decimal(
            request.POST.get("work_range", "")
        )

    except (InvalidOperation, TypeError):
        return JsonResponse(
            {
                "success": False,
                "message": "Please choose a valid work range.",
            },
            status=400,
        )

    allowed_ranges = {
        Decimal("5"),
        Decimal("10"),
        Decimal("15"),
        Decimal("20"),
        Decimal("25"),
        Decimal("30"),
        Decimal("50"),
    }

    if work_range not in allowed_ranges:
        return JsonResponse(
            {
                "success": False,
                "message": "Please choose an available work range.",
            },
            status=400,
        )

    worker = request.user.worker_profile

    worker.work_range = work_range

    worker.save(
        update_fields=["work_range"]
    )

    return JsonResponse(
        {
            "success": True,
            "message": f"Work range updated to {work_range} KM.",
        }
    )
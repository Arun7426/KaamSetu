from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation

from .forms import CustomerRegistrationForm
from .models import CustomerProfile
from bookings.models import Booking, Review


# ==========================
# Role Selection Page
# ==========================
def choose_role(request):

    return render(
        request,
        "choose_role.html"
    )


# ==========================
# Customer Registration
# ==========================
def register(request):

    if request.method == "POST":

        form = CustomerRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            CustomerProfile.objects.create(
                user=user,
                mobile=form.cleaned_data["mobile"]
            )

            login(request, user)

            return redirect("home")

    else:

        form = CustomerRegistrationForm()

    return render(
        request,
        "register.html",
        {
            "form": form
        }
    )


# ==========================
# Login
# ==========================
def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        selected_role = request.POST.get("role")

        # ==========================
        # Validate selected role
        # ==========================

        if selected_role not in ["customer", "worker"]:

            messages.error(
                request,
                "Please select Customer or Worker."
            )

            return render(
                request,
                "login.html"
            )

        # ==========================
        # Authenticate credentials
        # ==========================

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:

            messages.error(
                request,
                "Invalid Username or Password"
            )

            return render(
                request,
                "login.html"
            )

        # ==========================
        # Admin
        # ==========================

        if user.is_staff:

            login(request, user)

            return redirect("/admin/")

        # ==========================
        # Worker Login
        # ==========================

        if selected_role == "worker":

            if not hasattr(user, "worker_profile"):

                messages.error(
                    request,
                    "यह Customer account है। कृपया Customer option select करें।"
                )

                return render(
                    request,
                    "login.html"
                )

            login(request, user)

            return redirect("home")

        # ==========================
        # Customer Login
        # ==========================

        if selected_role == "customer":

            if not hasattr(user, "customer_profile"):

                messages.error(
                    request,
                    "यह Worker account है। कृपया Worker option select करें।"
                )

                return render(
                    request,
                    "login.html"
                )

            login(request, user)

            return redirect("home")

    return render(
        request,
        "login.html"
    )


# ==========================
# Logout
# ==========================
def user_logout(request):

    logout(request)

    return redirect("home")


# ==========================
# Customer Dashboard
# ==========================
@login_required
def customer_dashboard(request):

    bookings = Booking.objects.select_related(
        "worker"
    ).filter(
        customer=request.user
    ).order_by("-created_at")

    reviewed_booking_ids = set(
        Review.objects.filter(
            customer=request.user
        ).values_list("booking_id", flat=True)
    )

    review_ratings = {
        review.booking_id: review.rating
        for review in Review.objects.filter(customer=request.user)
    }

    for booking in bookings:
        booking.has_review = booking.id in reviewed_booking_ids
        booking.review_rating = review_ratings.get(booking.id)

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

    cancelled_bookings = bookings.filter(
        status="Cancelled"
    ).count()

    return render(
        request,
        "customer_dashboard.html",
        {
            "bookings": bookings,
            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "accepted_bookings": accepted_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings,
        }
    )


@login_required
@require_POST
def update_customer_location(request):
    """Save a customer's browser-provided coordinates for nearby-worker search."""

    if hasattr(request.user, "worker_profile"):

        return JsonResponse(
            {
                "success": False,
                "message": "Only customers can update this location."
            },
            status=403
        )

    try:

        latitude = Decimal(
            request.POST.get("latitude", "")
        )

        longitude = Decimal(
            request.POST.get("longitude", "")
        )

    except (InvalidOperation, TypeError):

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid location coordinates received."
            },
            status=400
        )

    if (
        not latitude.is_finite()
        or not longitude.is_finite()
        or not (-90 <= latitude <= 90 and -180 <= longitude <= 180)
    ):

        return JsonResponse(
            {
                "success": False,
                "message": "Location coordinates are outside the valid range."
            },
            status=400
        )

    profile = request.user.customer_profile

    changed = (
        profile.latitude != latitude
        or profile.longitude != longitude
    )

    profile.latitude = latitude
    profile.longitude = longitude

    profile.save(
        update_fields=[
            "latitude",
            "longitude"
        ]
    )

    return JsonResponse(
        {
            "success": True,
            "changed": changed,
            "message": "Your location has been updated."
        }
    )
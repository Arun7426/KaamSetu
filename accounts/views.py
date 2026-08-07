from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            # Admin
            if user.is_staff:
                return redirect("/admin/")

            # Worker
            elif hasattr(user, "worker_profile"):
                return redirect("home")

            # Customer
            else:
                return redirect("home")

        else:
            messages.error(
                request,
                "Invalid Username or Password"
            )

    return render(request, "login.html")


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
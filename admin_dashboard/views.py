from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.contrib.auth.models import User

from workers.models import Worker
from bookings.models import Booking
from payments.models import WorkerLedger


def staff_required(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(staff_required, login_url="login")
def admin_dashboard(request):

    # -----------------------------------------
    # USER COUNTS
    # -----------------------------------------

    total_users = User.objects.count()

    total_workers = Worker.objects.count()

    total_customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).count()


    # -----------------------------------------
    # BOOKING COUNTS
    # -----------------------------------------

    total_bookings = Booking.objects.count()

    pending_bookings = Booking.objects.filter(
        status="Pending"
    ).count()

    accepted_bookings = Booking.objects.filter(
        status="Accepted"
    ).count()

    completed_bookings = Booking.objects.filter(
        status="Completed"
    ).count()

    cancelled_bookings = Booking.objects.filter(
        status="Cancelled"
    ).count()


    # -----------------------------------------
    # PAYMENT / LEDGER
    # -----------------------------------------

    total_outstanding = sum(
        entry.amount
        for entry in WorkerLedger.objects.filter(
            transaction_type="Booking Fee",
            status="Pending"
        )
    )

    total_paid = sum(
        entry.amount
        for entry in WorkerLedger.objects.filter(
            transaction_type="Booking Fee",
            status="Paid"
        )
    )


    # -----------------------------------------
    # RECENT BOOKINGS
    # -----------------------------------------

    recent_bookings = Booking.objects.select_related(
        "worker",
        "customer"
    ).order_by(
        "-created_at"
    )[:10]


    return render(
        request,
        "admin_dashboard/dashboard.html",
        {
            "total_users": total_users,
            "total_workers": total_workers,
            "total_customers": total_customers,

            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "accepted_bookings": accepted_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings,

            "total_outstanding": total_outstanding,
            "total_paid": total_paid,

            "recent_bookings": recent_bookings,
        }
    )

@user_passes_test(staff_required, login_url="login")
def admin_workers(request):

    workers = Worker.objects.select_related(
        "user"
    ).order_by(
        "name"
    )

    return render(
        request,
        "admin_dashboard/workers.html",
        {
            "workers": workers,
        }
    )

@user_passes_test(staff_required, login_url="login")
def admin_customers(request):

    customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).order_by(
        "username"
    )

    return render(
        request,
        "admin_dashboard/customers.html",
        {
            "customers": customers,
        }
    )

@user_passes_test(staff_required, login_url="login")
def admin_bookings(request):

    bookings = Booking.objects.select_related(
        "worker",
        "customer"
    ).order_by(
        "-created_at"
    )

    status_filter = request.GET.get("status")

    if status_filter in [
        "Pending",
        "Accepted",
        "Completed",
        "Cancelled",
    ]:
        bookings = bookings.filter(
            status=status_filter
        )

    return render(
        request,
        "admin_dashboard/bookings.html",
        {
            "bookings": bookings,
            "status_filter": status_filter,
        }
    )
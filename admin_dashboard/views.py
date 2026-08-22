from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.db.models import Sum, Q
from django.core.exceptions import PermissionDenied

from functools import wraps

from workers.models import Worker
from bookings.models import Booking
from payments.models import WorkerLedger


# =========================================================
# EXISTING STAFF CHECK
# =========================================================

def staff_required(user):
    return user.is_authenticated and user.is_staff


# =========================================================
# KAAMSETU ADMIN ROLE
# =========================================================

def get_admin_role(user):
    """
    Two-level KaamSetu Admin architecture.

    SUPER_ADMIN:
        Django superuser

    ADMIN:
        Django staff user who is not a superuser

    NONE:
        Any other user
    """

    if not user or not user.is_authenticated:
        return "NONE"

    if user.is_superuser:
        return "SUPER_ADMIN"

    if user.is_staff:
        return "ADMIN"

    return "NONE"


# =========================================================
# KAAMSETU ADMIN ROLE FOUNDATION
# =========================================================

def admin_required(view_func):
    """
    Allow only KaamSetu Admin or Super Admin users.

    Super Admin:
        is_superuser = True

    Admin:
        is_staff = True
        is_superuser = False
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        # -------------------------------------------------
        # SUPER ADMIN
        # -------------------------------------------------

        if request.user.is_superuser:
            return view_func(
                request,
                *args,
                **kwargs
            )

        # -------------------------------------------------
        # NORMAL ADMIN
        # -------------------------------------------------

        if request.user.is_staff:
            return view_func(
                request,
                *args,
                **kwargs
            )

        # -------------------------------------------------
        # CUSTOMER / WORKER / NORMAL USER
        # -------------------------------------------------

        raise PermissionDenied(
            "You do not have permission to access the KaamSetu Admin Panel."
        )

    return wrapper


# =========================================================
# KAAMSETU PERMISSION REQUIRED
# =========================================================

def permission_required(permission_name):
    """
    Allow Super Admin automatically.

    Normal Admin users must have the
    specified Django permission.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            # -------------------------------------------------
            # SUPER ADMIN
            # -------------------------------------------------

            if request.user.is_superuser:
                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            # -------------------------------------------------
            # NORMAL ADMIN
            # -------------------------------------------------

            if (
                request.user.is_staff
                and request.user.has_perm(permission_name)
            ):
                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            raise PermissionDenied(
                "You do not have permission to access this section."
            )

        return wrapper

    return decorator


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_required
def admin_dashboard(request):

    role = get_admin_role(request.user)

    # =====================================================
    # USER COUNTS
    # =====================================================

    total_users = User.objects.count()

    total_workers = Worker.objects.count()

    total_customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).count()

    # =====================================================
    # BOOKING COUNTS
    # =====================================================

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

    # =====================================================
    # FINANCE
    # SUPER ADMIN ONLY
    # =====================================================

    total_outstanding = None
    total_paid = None

    workers_with_outstanding = Worker.objects.none()
    recent_payments = WorkerLedger.objects.none()

    if request.user.is_superuser:

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

        workers_with_outstanding = Worker.objects.annotate(
            outstanding=Sum(
                "ledger_entries__amount",
                filter=Q(
                    ledger_entries__transaction_type="Booking Fee",
                    ledger_entries__status="Pending"
                )
            )
        ).filter(
            outstanding__gt=0
        ).order_by(
            "-outstanding"
        )

        recent_payments = WorkerLedger.objects.select_related(
            "worker",
            "booking"
        ).order_by(
            "-created_at"
        )[:5]

    # =====================================================
    # RECENT BOOKINGS
    # =====================================================

    recent_bookings = Booking.objects.select_related(
        "worker",
        "customer"
    ).order_by(
        "-created_at"
    )[:10]

    # =====================================================
    # RECENT CUSTOMERS
    # =====================================================

    recent_customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).order_by(
        "-date_joined"
    )[:5]

    # =====================================================
    # RECENT WORKERS
    # =====================================================

    recent_workers = Worker.objects.select_related(
        "user"
    ).order_by(
        "-user__date_joined"
    )[:5]

    return render(
        request,
        "admin_dashboard/dashboard.html",
        {
            "admin_role": role,

            # -------------------------------------------------
            # USER STATISTICS
            # -------------------------------------------------

            "total_users": total_users,
            "total_workers": total_workers,
            "total_customers": total_customers,

            # -------------------------------------------------
            # BOOKING STATISTICS
            # -------------------------------------------------

            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "accepted_bookings": accepted_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings,

            # -------------------------------------------------
            # FINANCE
            # SUPER ADMIN ONLY
            # -------------------------------------------------

            "total_outstanding": total_outstanding,
            "total_paid": total_paid,
            "workers_with_outstanding":
                workers_with_outstanding,
            "recent_payments":
                recent_payments,

            # -------------------------------------------------
            # RECENT ACTIVITY
            # -------------------------------------------------

            "recent_bookings":
                recent_bookings,
            "recent_customers":
                recent_customers,
            "recent_workers":
                recent_workers,
        }
    )


# =========================================================
# WORKERS
# =========================================================

@permission_required("workers.view_worker")
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


# =========================================================
# CUSTOMERS
# =========================================================

@permission_required("auth.view_user")
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


# =========================================================
# BOOKINGS
# =========================================================

@permission_required("bookings.view_booking")
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


# =========================================================
# PAYMENTS
# =========================================================

@permission_required("payments.view_workerledger")
def admin_payments(request):

    ledger_entries = WorkerLedger.objects.select_related(
        "worker",
        "booking"
    ).order_by(
        "-created_at"
    )

    status_filter = request.GET.get("status")

    if status_filter in [
        "Pending",
        "Paid",
    ]:
        ledger_entries = ledger_entries.filter(
            status=status_filter
        )

    transaction_filter = request.GET.get("transaction")

    if transaction_filter in [
        "Booking Fee",
        "Payment",
    ]:
        ledger_entries = ledger_entries.filter(
            transaction_type=transaction_filter
        )

    return render(
        request,
        "admin_dashboard/payments.html",
        {
            "ledger_entries": ledger_entries,
            "status_filter": status_filter,
            "transaction_filter": transaction_filter,
        }
    )


# =========================================================
# SUPER ADMIN ONLY
# ADMIN MANAGEMENT SECURITY
# =========================================================

def super_admin_required(view_func):
    """
    Allow ONLY Django Super Admin users.

    Normal Admin users are explicitly denied.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superuser:
            raise PermissionDenied(
                "Only Super Admin can access Admin Management."
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# =========================================================
# ADMIN MANAGEMENT
# SUPER ADMIN ONLY
# =========================================================

@super_admin_required
def admin_management(request):

    # -----------------------------------------------------
    # ONLY NORMAL ADMINS
    #
    # Super Admin itself is not included in this list.
    # -----------------------------------------------------

    admins = User.objects.filter(
        is_staff=True,
        is_superuser=False
    ).prefetch_related(
        "groups",
        "user_permissions"
    ).order_by(
        "username"
    )

    # -----------------------------------------------------
    # ALL AVAILABLE GROUPS
    # -----------------------------------------------------

    groups = Group.objects.all().order_by(
        "name"
    )

    return render(
        request,
        "admin_dashboard/admin_management.html",
        {
            "admins": admins,
            "groups": groups,
        }
    )
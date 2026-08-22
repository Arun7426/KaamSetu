from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import render, redirect, get_object_or_404


# =========================================================
# SUPER ADMIN SECURITY
# =========================================================

def super_admin_required(view_func):
    """
    Allow ONLY Django Super Admin users.

    Normal Admin users are explicitly denied.
    """

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superuser:
            raise PermissionDenied(
                "Only Super Admin can manage Admin accounts."
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# =========================================================
# CREATE ADMIN
# =========================================================

@super_admin_required
def create_admin(request):

    groups = Group.objects.all().order_by("name")

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        username = request.POST.get(
            "username",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        selected_group_ids = request.POST.getlist(
            "groups"
        )

        is_active = (
            request.POST.get("is_active") == "on"
        )

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not full_name:
            messages.error(
                request,
                "Full Name is required."
            )

            return render(
                request,
                "admin_dashboard/create_admin.html",
                {
                    "groups": groups,
                }
            )

        if not username:
            messages.error(
                request,
                "Username is required."
            )

            return render(
                request,
                "admin_dashboard/create_admin.html",
                {
                    "groups": groups,
                }
            )

        if User.objects.filter(
            username__iexact=username
        ).exists():

            messages.error(
                request,
                "This username is already in use."
            )

            return render(
                request,
                "admin_dashboard/create_admin.html",
                {
                    "groups": groups,
                }
            )

        if email and User.objects.filter(
            email__iexact=email
        ).exists():

            messages.error(
                request,
                "This email address is already in use."
            )

            return render(
                request,
                "admin_dashboard/create_admin.html",
                {
                    "groups": groups,
                }
            )

        # -------------------------------------------------
        # PASSWORD CONFIRMATION
        # -------------------------------------------------

        if not password:
            messages.error(
                request,
                "Password is required."
            )

            return render(
                request,
                "admin_dashboard/create_admin.html",
                {
                    "groups": groups,
                }
            )

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                "admin_dashboard/create_admin.html",
                {
                    "groups": groups,
                }
            )

        # -------------------------------------------------
        # DJANGO PASSWORD VALIDATION
        # -------------------------------------------------

        try:

            validate_password(
                password
            )

        except ValidationError as error:

            for message in error.messages:

                messages.error(
                    request,
                    message
                )

            return render(
                request,
                "admin_dashboard/create_admin.html",
                {
                    "groups": groups,
                }
            )

        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        admin_user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        admin_user.first_name = full_name

        # -------------------------------------------------
        # IMPORTANT ROLE SETTINGS
        # -------------------------------------------------

        admin_user.is_staff = True
        admin_user.is_superuser = False
        admin_user.is_active = is_active

        admin_user.save()

        # -------------------------------------------------
        # GROUP ASSIGNMENT
        # -------------------------------------------------

        selected_groups = Group.objects.filter(
            id__in=selected_group_ids
        )

        admin_user.groups.set(
            selected_groups
        )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        messages.success(
            request,
            f"Admin '{username}' created successfully."
        )

        return redirect(
            "admin_management"
        )

    # =====================================================
    # GET
    # =====================================================

    return render(
        request,
        "admin_dashboard/create_admin.html",
        {
            "groups": groups,
        }
    )


# =========================================================
# EDIT EXISTING ADMIN
# =========================================================

@super_admin_required
def edit_admin(request, user_id):
    """
    Allow ONLY Super Admin to edit an existing normal Admin.

    Super Admin accounts are intentionally excluded from the
    target queryset and therefore cannot be edited through this
    management screen.
    """

    admin_user = get_object_or_404(
        User,
        id=user_id,
        is_staff=True,
        is_superuser=False
    )

    groups = Group.objects.all().order_by("name")

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        selected_group_ids = request.POST.getlist(
            "groups"
        )

        is_active = (
            request.POST.get("is_active") == "on"
        )

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not full_name:

            messages.error(
                request,
                "Full Name is required."
            )

            return render(
                request,
                "admin_dashboard/edit_admin.html",
                {
                    "admin_user": admin_user,
                    "groups": groups,
                    "selected_group_ids": selected_group_ids,
                }
            )

        # -------------------------------------------------
        # EMAIL UNIQUENESS
        # -------------------------------------------------

        if email and User.objects.filter(
            email__iexact=email
        ).exclude(
            id=admin_user.id
        ).exists():

            messages.error(
                request,
                "This email address is already in use."
            )

            return render(
                request,
                "admin_dashboard/edit_admin.html",
                {
                    "admin_user": admin_user,
                    "groups": groups,
                    "selected_group_ids": selected_group_ids,
                }
            )

        # -------------------------------------------------
        # UPDATE BASIC DETAILS
        # -------------------------------------------------

        admin_user.first_name = full_name
        admin_user.email = email
        admin_user.is_active = is_active

        # Keep this account a normal Admin.
        admin_user.is_staff = True
        admin_user.is_superuser = False

        admin_user.save()

        # -------------------------------------------------
        # UPDATE PERMISSION GROUPS
        # -------------------------------------------------

        selected_groups = Group.objects.filter(
            id__in=selected_group_ids
        )

        admin_user.groups.set(
            selected_groups
        )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        messages.success(
            request,
            f"Admin '{admin_user.username}' updated successfully."
        )

        return redirect(
            "admin_management"
        )

    # =====================================================
    # GET
    # =====================================================

    return render(
        request,
        "admin_dashboard/edit_admin.html",
        {
            "admin_user": admin_user,
            "groups": groups,
        }
    )
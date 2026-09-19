import secrets
import traceback

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from django.conf import settings

from django.db.models import Sum

from decimal import Decimal
import razorpay

from django.db import transaction as db_transaction
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import CustomerProfile
from workers.models import Worker

from bookings.models import Booking, Review, Notification
from bookings.views import (
    get_customer_offer_suggestions,
    get_worker_counter_suggestions,
)
from bookings.notifications import create_notification
from payments.services import (
    can_worker_receive_booking,
    create_booking_fee,
    get_worker_outstanding,
    get_active_promotion,
    create_razorpay_order,
    verify_razorpay_payment,
)

from payments.models import (
    WorkerLedger,
    WorkerPaymentTransaction,
)
from .serializers import WorkerLedgerSerializer

from .models import MobileOTP
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    MobileRegistrationSerializer,
    WebsiteLoginSetupSerializer,
    WorkerListSerializer,
    WorkerDetailSerializer,
    CustomerProfileAPISerializer,
    WorkerProfileAPISerializer,
    BookingCreateSerializer,
    BookingSerializer,
    CustomerOfferSerializer,
    WorkerOfferResponseSerializer,
    CustomerCounterResponseSerializer,
    WorkerBookingStatusSerializer,
    ReviewCreateSerializer,
    WorkerPaymentInitiateSerializer,
    WorkerPaymentVerifySerializer,
    NotificationSerializer,
)
from .services import (
    create_mobile_otp,
    verify_mobile_otp,
)


@api_view(["GET"])
def api_status(request):
    return Response({
        "status": "success",
        "message": "KaamSetu API is working",
        "version": "v1",
    })


def get_account_by_mobile(mobile):

    customer = (
        CustomerProfile.objects
        .select_related("user")
        .filter(mobile=mobile)
        .first()
    )

    if customer:
        return customer.user, "customer"

    worker = (
        Worker.objects
        .select_related("user")
        .filter(mobile=mobile)
        .first()
    )

    if worker:
        return worker.user, "worker"

    return None, None


@api_view(["POST"])
def send_otp(request):

    serializer = SendOTPSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    mobile = serializer.validated_data["mobile"]
    purpose = serializer.validated_data["purpose"]
    role = serializer.validated_data.get("role")

    if purpose == "registration":

        if CustomerProfile.objects.filter(
            mobile=mobile
        ).exists():

            return Response(
                {
                    "status": "error",
                    "message": (
                        "This mobile number is already registered."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        if Worker.objects.filter(
            mobile=mobile
        ).exists():

            return Response(
                {
                    "status": "error",
                    "message": (
                        "This mobile number is already registered."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

    elif purpose == "login":

        user, detected_role = get_account_by_mobile(
            mobile
        )

        if user is None:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "No account found with this mobile number."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "This account has been blocked."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        role = detected_role

    elif purpose == "website_login_setup":

        user, detected_role = get_account_by_mobile(
            mobile
        )

        if user is None:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "No account found with this mobile number."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "This account has been blocked."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        role = detected_role

    try:

        otp_record, otp = create_mobile_otp(
            mobile=mobile,
            purpose=purpose,
            role=role or "customer",
        )

    except ValueError as exc:

        return Response(
            {
                "status": "error",
                "message": str(exc),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "status": "success",
            "message": "OTP generated successfully.",
            "otp_request_id": otp_record.id,
            "expires_at": otp_record.expires_at,
            "development_otp": otp,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def verify_otp(request):

    serializer = VerifyOTPSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    mobile = serializer.validated_data["mobile"]
    otp = serializer.validated_data["otp"]
    purpose = serializer.validated_data["purpose"]
    role = serializer.validated_data.get("role")

    if purpose in [
        "login",
        "website_login_setup",
    ]:

        user, detected_role = get_account_by_mobile(
            mobile
        )

        if user is None:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "No account found with this mobile number."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "This account has been blocked."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        role = detected_role

    try:

        otp_record = verify_mobile_otp(
            mobile=mobile,
            otp=otp,
            purpose=purpose,
            role=role,
        )

    except ValueError as exc:

        return Response(
            {
                "status": "error",
                "message": str(exc),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if purpose == "login":

        user, account_role = get_account_by_mobile(
            mobile
        )

        if user is None:
            return Response(
                {
                    "status": "error",
                    "message": "Account not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "This account has been blocked."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        token, created = Token.objects.get_or_create(
            user=user
        )

        return Response(
            {
                "status": "success",
                "message": "Login successful.",
                "token": token.key,
                "user_id": user.username,
                "mobile": mobile,
                "role": account_role,
                "website_login_enabled": (
                    user.has_usable_password()
                ),
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            "status": "success",
            "message": "OTP verified successfully.",
            "mobile": otp_record.mobile,
            "role": otp_record.role,
            "purpose": otp_record.purpose,
            "verified": True,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def register_mobile_user(request):

    serializer = MobileRegistrationSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data

    mobile = data["mobile"]
    role = data["role"]

    if CustomerProfile.objects.filter(
        mobile=mobile
    ).exists():

        return Response(
            {
                "status": "error",
                "message": (
                    "This mobile number is already registered."
                ),
            },
            status=status.HTTP_409_CONFLICT,
        )

    if Worker.objects.filter(
        mobile=mobile
    ).exists():

        return Response(
            {
                "status": "error",
                "message": (
                    "This mobile number is already registered."
                ),
            },
            status=status.HTTP_409_CONFLICT,
        )

    otp_record = (
        MobileOTP.objects.filter(
            mobile=mobile,
            purpose="registration",
            role=role,
            is_verified=True,
            consumed_at__isnull=True,
        )
        .order_by("-verified_at")
        .first()
    )

    if otp_record is None:
        return Response(
            {
                "status": "error",
                "message": (
                    "Mobile number is not verified. "
                    "Please verify OTP first."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if otp_record.is_expired():

        otp_record.consumed_at = timezone.now()

        otp_record.save(
            update_fields=["consumed_at"]
        )

        return Response(
            {
                "status": "error",
                "message": (
                    "OTP verification has expired. "
                    "Please request a new OTP."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():

        while True:

            username = (
                "KS"
                + secrets.token_hex(5).upper()
            )

            if not User.objects.filter(
                username=username
            ).exists():
                break

        user = User.objects.create(
            username=username,
        )

        user.set_unusable_password()

        user.first_name = data["name"]

        if data.get("email"):
            user.email = data["email"]

        user.save()

        if role == "customer":

            CustomerProfile.objects.create(
                user=user,
                mobile=mobile,
                mobile_verified=True,
                address=data.get(
                    "address",
                    "",
                ),
            )

        else:

            Worker.objects.create(
                user=user,
                name=data["name"],
                mobile=mobile,
                profession=data["profession"],
                experience=data["experience"],
                city=data["city"],
                area=data["area"],
                daily_wage=data["daily_wage"],
                about=data.get(
                    "about",
                    "",
                ),
            )

        otp_record.consumed_at = timezone.now()

        otp_record.save(
            update_fields=[
                "consumed_at",
            ]
        )

    return Response(
        {
            "status": "success",
            "message": (
                "Registration completed successfully."
            ),
            "user_id": username,
            "role": role,
            "mobile": mobile,
            "website_login_enabled": False,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def current_user(request):

    user = request.user

    customer = (
        CustomerProfile.objects
        .filter(user=user)
        .first()
    )

    if customer:

        return Response(
            {
                "status": "success",
                "user_id": user.username,
                "mobile": customer.mobile,
                "role": "customer",
                "name": user.first_name,
                "email": user.email,
                "website_login_enabled": (
                    user.has_usable_password()
                ),
            },
            status=status.HTTP_200_OK,
        )

    worker = (
        Worker.objects
        .filter(user=user)
        .first()
    )

    if worker:

        return Response(
            {
                "status": "success",
                "user_id": user.username,
                "mobile": worker.mobile,
                "role": "worker",
                "name": worker.name,
                "email": user.email,
                "website_login_enabled": (
                    user.has_usable_password()
                ),
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            "status": "error",
            "message": "Account profile not found.",
        },
        status=status.HTTP_404_NOT_FOUND,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def setup_website_login(request):

    user = request.user

    if user.has_usable_password():

        return Response(
            {
                "status": "error",
                "message": (
                    "Website login is already enabled."
                ),
                "user_id": user.username,
                "website_login_enabled": True,
            },
            status=status.HTTP_409_CONFLICT,
        )

    serializer = WebsiteLoginSetupSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            {
                "status": "error",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    password = serializer.validated_data["password"]

    user.set_password(password)

    user.save(
        update_fields=["password"]
    )

    return Response(
        {
            "status": "success",
            "message": (
                "Website login enabled successfully."
            ),
            "user_id": user.username,
            "website_login_enabled": True,
        },
        status=status.HTTP_200_OK,
    )


# =========================================================
# MODULE 2 — WORKER DISCOVERY / SEARCH API
# =========================================================

@api_view(["GET"])
def worker_list(request):

    workers = (
        Worker.objects
        .select_related("user")
        .all()
    )

    available = request.GET.get(
        "available",
        "true",
    ).strip().lower()

    if available in ["true", "1", "yes"]:
        workers = workers.filter(
            available=True
        )

    elif available in ["false", "0", "no"]:
        workers = workers.filter(
            available=False
        )

    profession = request.GET.get(
        "profession"
    )

    if profession:
        workers = workers.filter(
            profession__iexact=profession.strip()
        )

    city = request.GET.get(
        "city"
    )

    if city:
        workers = workers.filter(
            city__icontains=city.strip()
        )

    area = request.GET.get(
        "area"
    )

    if area:
        workers = workers.filter(
            area__icontains=area.strip()
        )

    search = request.GET.get(
        "search"
    )

    if search:
        search = search.strip()

        workers = workers.filter(
            name__icontains=search
        ) | workers.filter(
            profession__icontains=search
        ) | workers.filter(
            city__icontains=search
        ) | workers.filter(
            area__icontains=search
        )

    min_rating = request.GET.get(
        "min_rating"
    )

    if min_rating:

        try:
            workers = workers.filter(
                rating__gte=float(min_rating)
            )

        except (TypeError, ValueError):
            return Response(
                {
                    "status": "error",
                    "message": (
                        "min_rating must be a valid number."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    max_wage = request.GET.get(
        "max_wage"
    )

    if max_wage:

        try:
            workers = workers.filter(
                daily_wage__lte=float(max_wage)
            )

        except (TypeError, ValueError):
            return Response(
                {
                    "status": "error",
                    "message": (
                        "max_wage must be a valid number."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    workers = workers.order_by(
        "-vverified",
        "-rating",
        "daily_wage",
        "name",
    )

    serializer = WorkerListSerializer(
        workers,
        many=True,
        context={
            "request": request,
        },
    )

    return Response(
        {
            "status": "success",
            "count": workers.count(),
            "results": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def worker_detail(request, worker_id):

    worker = (
        Worker.objects
        .select_related("user")
        .filter(id=worker_id)
        .first()
    )

    if worker is None:

        return Response(
            {
                "status": "error",
                "message": "Worker not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = WorkerDetailSerializer(
        worker,
        context={
            "request": request,
        },
    )

    return Response(
        {
            "status": "success",
            "worker": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


# =========================================================
# MODULE 3 — CUSTOMER & WORKER PROFILE API
# =========================================================

@api_view(["GET", "PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_profile(request):

    user = request.user

    customer = (
        CustomerProfile.objects
        .filter(user=user)
        .first()
    )

    worker = (
        Worker.objects
        .filter(user=user)
        .first()
    )

    # -------------------------------------------------
    # CUSTOMER PROFILE
    # -------------------------------------------------

    if customer:

        if request.method == "GET":

            data = {
                "user_id": user.username,
                "role": "customer",
                "mobile": customer.mobile,
                "mobile_verified": customer.mobile_verified,
                "name": user.first_name,
                "email": user.email,
                "address": customer.address,
                "latitude": customer.latitude,
                "longitude": customer.longitude,
            }

            return Response(
                {
                    "status": "success",
                    "profile": data,
                },
                status=status.HTTP_200_OK,
            )

        serializer = CustomerProfileAPISerializer(
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():

            return Response(
                {
                    "status": "error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        if "name" in data:
            user.first_name = data["name"]

        if "email" in data:
            user.email = data["email"]

        user.save(
            update_fields=[
                "first_name",
                "email",
            ]
        )

        if "address" in data:
            customer.address = data["address"]

        if "latitude" in data:
            customer.latitude = data["latitude"]

        if "longitude" in data:
            customer.longitude = data["longitude"]

        customer.save()

        return Response(
            {
                "status": "success",
                "message": (
                    "Customer profile updated successfully."
                ),
                "profile": {
                    "user_id": user.username,
                    "role": "customer",
                    "mobile": customer.mobile,
                    "mobile_verified": customer.mobile_verified,
                    "name": user.first_name,
                    "email": user.email,
                    "address": customer.address,
                    "latitude": customer.latitude,
                    "longitude": customer.longitude,
                },
            },
            status=status.HTTP_200_OK,
        )

    # -------------------------------------------------
    # WORKER PROFILE
    # -------------------------------------------------

    if worker:

        if request.method == "GET":

            serializer = WorkerProfileAPISerializer()

            return Response(
                {
                    "status": "success",
                    "profile": {
                        "user_id": user.username,
                        "role": "worker",
                        "mobile": worker.mobile,
                        "name": worker.name,
                        "email": user.email,
                        "profession": worker.profession,
                        "experience": worker.experience,
                        "city": worker.city,
                        "area": worker.area,
                        "latitude": worker.latitude,
                        "longitude": worker.longitude,
                        "work_range": worker.work_range,
                        "daily_wage": worker.daily_wage,
                        "about": worker.about,
                        "available": worker.available,
                        "profile_photo": (
                            request.build_absolute_uri(
                                worker.profile_photo.url
                            )
                            if worker.profile_photo
                            else None
                        ),
                    },
                },
                status=status.HTTP_200_OK,
            )

        serializer = WorkerProfileAPISerializer(
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():

            return Response(
                {
                    "status": "error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        if "name" in data:
            worker.name = data["name"]
            user.first_name = data["name"]

        if "email" in data:
            user.email = data["email"]

        worker_fields = [
            "profession",
            "experience",
            "city",
            "area",
            "latitude",
            "longitude",
            "work_range",
            "daily_wage",
            "about",
            "available",
            "profile_photo",
        ]

        for field in worker_fields:

            if field in data:
                setattr(
                    worker,
                    field,
                    data[field],
                )

        user.save(
            update_fields=[
                "first_name",
                "email",
            ]
        )

        worker.save()

        return Response(
            {
                "status": "success",
                "message": (
                    "Worker profile updated successfully."
                ),
                "profile": {
                    "user_id": user.username,
                    "role": "worker",
                    "mobile": worker.mobile,
                    "name": worker.name,
                    "email": user.email,
                    "profession": worker.profession,
                    "experience": worker.experience,
                    "city": worker.city,
                    "area": worker.area,
                    "latitude": worker.latitude,
                    "longitude": worker.longitude,
                    "work_range": worker.work_range,
                    "daily_wage": worker.daily_wage,
                    "about": worker.about,
                    "available": worker.available,
                    "profile_photo": (
                        request.build_absolute_uri(
                            worker.profile_photo.url
                        )
                        if worker.profile_photo
                        else None
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            "status": "error",
            "message": "Account profile not found.",
        },
        status=status.HTTP_404_NOT_FOUND,
    )

# =========================================================
# MODULE 7 — PAYMENTS API
# =========================================================


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def worker_payment_summary(request):
    """
    Return payment summary for the authenticated worker.

    Financial information is strictly limited to the
    worker's own account.
    """

    # -----------------------------------------------------
    # WORKER ONLY
    # -----------------------------------------------------

    try:
        worker = request.user.worker_profile
    except AttributeError:
        return Response(
            {
                "status": "error",
                "message": "Only workers can access payment information.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # -----------------------------------------------------
    # OUTSTANDING
    # -----------------------------------------------------

    outstanding = get_worker_outstanding(worker)

    # -----------------------------------------------------
    # SUCCESSFUL BOOKINGS
    # -----------------------------------------------------

    successful_bookings = Booking.objects.filter(
        worker=worker,
        negotiation_status="Accepted",
    ).count()

    # -----------------------------------------------------
    # PROMOTION / FREE BOOKINGS
    # -----------------------------------------------------

    promotion = get_active_promotion()

    if promotion:
        free_booking_limit = promotion.free_bookings_limit
    else:
        free_booking_limit = 0

    free_bookings_used = min(
        successful_bookings,
        free_booking_limit,
    )

    free_bookings_remaining = max(
        free_booking_limit - successful_bookings,
        0,
    )

    chargeable_bookings = max(
        successful_bookings - free_booking_limit,
        0,
    )

    # -----------------------------------------------------
    # LEDGER TOTALS
    # -----------------------------------------------------

    booking_fee_total = (
        WorkerLedger.objects.filter(
            worker=worker,
            transaction_type="Booking Fee",
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    pending_fee_total = (
        WorkerLedger.objects.filter(
            worker=worker,
            transaction_type="Booking Fee",
            status="Pending",
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    paid_fee_total = (
        WorkerLedger.objects.filter(
            worker=worker,
            transaction_type="Booking Fee",
            status="Paid",
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # -----------------------------------------------------
    # BOOKING ELIGIBILITY
    # -----------------------------------------------------

    can_receive_booking = can_worker_receive_booking(
        worker
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return Response(
        {
            "status": "success",
            "payment_summary": {
                "currency": "INR",

                "successful_bookings": successful_bookings,

                "free_booking_limit": free_booking_limit,
                "free_bookings_used": free_bookings_used,
                "free_bookings_remaining": free_bookings_remaining,

                "chargeable_bookings": chargeable_bookings,

                "total_booking_fees": booking_fee_total,
                "pending_fees": pending_fee_total,
                "paid_fees": paid_fee_total,

                "outstanding": outstanding,
                "outstanding_limit": "200.00",

                "can_receive_booking": can_receive_booking,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def initiate_worker_payment(request):
    """
    Initiate a Razorpay payment for the authenticated worker's
    outstanding platform fees.
    """

    try:
        worker = request.user.worker_profile
    except AttributeError:
        return Response(
            {
                "status": "error",
                "message": "Only workers can initiate payments."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = WorkerPaymentInitiateSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    amount = serializer.validated_data["amount"]

    outstanding = get_worker_outstanding(worker)

    if outstanding <= 0:
        return Response(
            {
                "status": "error",
                "message": "You have no outstanding payment."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if amount > outstanding:
        return Response(
            {
                "status": "error",
                "message": (
                    "Payment amount cannot exceed "
                    "outstanding amount."
                ),
                "outstanding": str(outstanding)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    with db_transaction.atomic():

        payment_transaction = WorkerPaymentTransaction.objects.create(
            worker=worker,
            amount=amount,
            status="Created",
            provider="Razorpay"
        )

        try:
            razorpay_order = create_razorpay_order(
                worker=worker,
                amount=amount,
                transaction=payment_transaction
            )

        except Exception as exc:
            print("\n========== RAZORPAY ORDER ERROR ==========")
            print(f"Error Type: {type(exc).__name__}")
            print(f"Error: {exc}")
            traceback.print_exc()
            print("==========================================\n")

            payment_transaction.status = "Failed"

            payment_transaction.save(
                update_fields=[
                    "status",
                    "updated_at"
                ]
            )

            return Response(
                {
                    "status": "error",
                    "message": "Unable to create Razorpay payment order."
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

    return Response(
        {
            "status": "success",
            "payment": {
                "transaction_id": payment_transaction.id,
                "provider": "Razorpay",
                "order_id": razorpay_order["id"],
                "amount": str(amount),
                "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID,
                "status": payment_transaction.status,
            }
        },
        status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def verify_worker_payment(request):
    """
    Verify a Razorpay payment for the authenticated worker.

    The payment is verified using Razorpay's server-side
    signature verification mechanism.
    """

    # -----------------------------------------
    # WORKER ONLY
    # -----------------------------------------

    try:
        worker = request.user.worker_profile
    except AttributeError:
        return Response(
            {
                "status": "error",
                "message": "Only workers can verify payments."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # -----------------------------------------
    # VALIDATE REQUEST
    # -----------------------------------------

    serializer = WorkerPaymentVerifySerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    data = serializer.validated_data

    transaction_id = data["transaction_id"]
    razorpay_order_id = data["razorpay_order_id"]
    razorpay_payment_id = data["razorpay_payment_id"]
    razorpay_signature = data["razorpay_signature"]

    # -----------------------------------------
    # FIND TRANSACTION
    # Lock row to prevent duplicate verification
    # -----------------------------------------

    payment_transaction = (
        WorkerPaymentTransaction.objects
        .select_for_update()
        .filter(
            id=transaction_id,
            worker=worker,
        )
        .first()
    )

    if payment_transaction is None:
        return Response(
            {
                "status": "error",
                "message": "Payment transaction not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------------------------
    # IDEMPOTENCY
    # -----------------------------------------

    if payment_transaction.status == "Verified":
        return Response(
            {
                "status": "success",
                "message": "Payment is already verified.",
                "payment": {
                    "transaction_id": payment_transaction.id,
                    "provider": payment_transaction.provider,
                    "order_id": payment_transaction.provider_order_id,
                    "payment_id": payment_transaction.provider_payment_id,
                    "amount": str(payment_transaction.amount),
                    "currency": "INR",
                    "status": payment_transaction.status,
                }
            },
            status=status.HTTP_200_OK
        )

    # -----------------------------------------
    # ORDER ID MATCH
    # -----------------------------------------

    if payment_transaction.provider_order_id != razorpay_order_id:
        return Response(
            {
                "status": "error",
                "message": "Razorpay order ID does not match."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------
    # ONLY PENDING TRANSACTIONS
    # -----------------------------------------

    if payment_transaction.status != "Pending":
        return Response(
            {
                "status": "error",
                "message": (
                    f"Payment cannot be verified from "
                    f"current status: {payment_transaction.status}."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------
    # RAZORPAY SERVER-SIDE SIGNATURE VERIFICATION
    # -----------------------------------------

    try:

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

        verify_razorpay_payment(
            order_id=razorpay_order_id,
            payment_id=razorpay_payment_id,
            signature=razorpay_signature,
            expected_amount=payment_transaction.amount,
        )

    except razorpay.errors.SignatureVerificationError:

        payment_transaction.status = "Failed"

        payment_transaction.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "status": "error",
                "message": "Payment signature verification failed."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as exc:

        print("\n========== RAZORPAY VERIFICATION ERROR ==========")
        print(f"Error Type: {type(exc).__name__}")
        print(f"Error: {exc}")
        traceback.print_exc()
        print("==================================================\n")

        return Response(
            {
                "status": "error",
                "message": "Unable to verify Razorpay payment."
            },
            status=status.HTTP_502_BAD_GATEWAY
        )

    # -----------------------------------------
    # PAYMENT VERIFIED
    # -----------------------------------------

    payment_transaction.provider_payment_id = (
        razorpay_payment_id
    )

    payment_transaction.status = "Verified"

    payment_transaction.save(
        update_fields=[
            "provider_payment_id",
            "status",
            "updated_at",
        ]
    )

    return Response(
        {
            "status": "success",
            "message": "Payment verified successfully.",
            "payment": {
                "transaction_id": payment_transaction.id,
                "provider": payment_transaction.provider,
                "order_id": payment_transaction.provider_order_id,
                "payment_id": payment_transaction.provider_payment_id,
                "amount": str(payment_transaction.amount),
                "currency": "INR",
                "status": payment_transaction.status,
            }
        },
        status=status.HTTP_200_OK
    )

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def worker_payment_ledger(request):
    """
    Return the authenticated worker's own payment ledger.
    """

    try:
        worker = request.user.worker_profile
    except AttributeError:
        return Response(
            {
                "status": "error",
                "message": "Only workers can access payment information.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    ledger_entries = (
        WorkerLedger.objects
        .filter(worker=worker)
        .select_related("booking")
        .order_by("-created_at")
    )

    data = []

    for entry in ledger_entries:
        data.append(
            {
                "id": entry.id,
                "transaction_type": entry.transaction_type,
                "amount": float(entry.amount),
                "status": entry.status,
                "description": entry.description,
                "created_at": entry.created_at.isoformat(),
                "paid_at": (
                    entry.paid_at.isoformat()
                    if entry.paid_at
                    else None
                ),
                "booking_id": (
                    entry.booking.id
                    if entry.booking
                    else None
                ),
            }
        )

    return Response(
        {
            "status": "success",
            "ledger": data,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def worker_payment_history(request):
    """
    Return payment transactions made by the authenticated worker.
    """

    try:
        worker = request.user.worker_profile
    except AttributeError:
        return Response(
            {
                "status": "error",
                "message": "Only workers can access payment information.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    payment_entries = (
        WorkerLedger.objects
        .filter(
            worker=worker,
            transaction_type="Payment",
        )
        .order_by("-paid_at", "-created_at")
    )

    data = []

    for entry in payment_entries:
        data.append(
            {
                "id": entry.id,
                "amount": float(entry.amount),
                "status": entry.status,
                "description": entry.description,
                "created_at": entry.created_at.isoformat(),
                "paid_at": (
                    entry.paid_at.isoformat()
                    if entry.paid_at
                    else None
                ),
            }
        )

    return Response(
        {
            "status": "success",
            "payment_history": data,
        },
        status=status.HTTP_200_OK,
    )

# =========================================================
# MODULE 4 — BOOKING API
# =========================================================


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_booking(request):

    # Only customers can create bookings.
    if hasattr(request.user, "worker_profile"):
        return Response(
            {
                "status": "error",
                "message": "Only customers can create bookings.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    customer = CustomerProfile.objects.filter(
        user=request.user
    ).first()

    if customer is None:
        return Response(
            {
                "status": "error",
                "message": "Customer profile not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = BookingCreateSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data

    worker = (
        Worker.objects
        .select_related("user")
        .filter(id=data["worker_id"])
        .first()
    )

    if worker is None:
        return Response(
            {
                "status": "error",
                "message": "Worker not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Respect existing platform rule:
    # worker with outstanding >= ₹200 cannot receive new bookings.
    if not can_worker_receive_booking(worker):
        return Response(
            {
                "status": "error",
                "message": (
                    "This worker is currently not accepting "
                    "new bookings."
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    customer_name = (
        request.user.get_full_name()
        or request.user.first_name
        or request.user.username
    )

    customer_mobile = customer.mobile or ""

    booking = Booking.objects.create(
        worker=worker,
        customer=request.user,
        customer_name=customer_name,
        customer_mobile=customer_mobile,
        customer_address=data["customer_address"],
        work_date=data["work_date"],
        work_description=data["work_description"],
        status="Pending",
        original_amount=int(worker.daily_wage),
    )

    # Notify worker about the new booking request.
    create_notification(
        recipient=worker.user,
        booking=booking,
        notification_type="booking",
        message=(
            f"New booking request from "
            f"{booking.customer_name}."
        ),
    )

    response_serializer = BookingSerializer(
        booking,
        context={"request": request},
    )

    return Response(
        {
            "status": "success",
            "message": "Booking request created successfully.",
            "booking": response_serializer.data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def booking_list(request):

    user = request.user

    # Customer → show customer's bookings.
    if hasattr(user, "customer_profile"):

        bookings = (
            Booking.objects
            .select_related("worker")
            .filter(customer=user)
            .order_by("-created_at")
        )

    # Worker → show bookings received by that worker.
    elif hasattr(user, "worker_profile"):

        bookings = (
            Booking.objects
            .select_related("customer")
            .filter(worker=user.worker_profile)
            .order_by("-created_at")
        )

    else:
        return Response(
            {
                "status": "error",
                "message": "Account profile not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = BookingSerializer(
        bookings,
        many=True,
        context={"request": request},
    )

    return Response(
        {
            "status": "success",
            "count": bookings.count(),
            "results": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def booking_detail(request, booking_id):

    user = request.user

    # Customer → can only see own booking.
    if hasattr(user, "customer_profile"):

        booking = (
            Booking.objects
            .select_related("worker")
            .filter(
                id=booking_id,
                customer=user,
            )
            .first()
        )

    # Worker → can only see bookings assigned to that worker.
    elif hasattr(user, "worker_profile"):

        booking = (
            Booking.objects
            .select_related("customer")
            .filter(
                id=booking_id,
                worker=user.worker_profile,
            )
            .first()
        )

    else:
        return Response(
            {
                "status": "error",
                "message": "Account profile not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if booking is None:
        return Response(
            {
                "status": "error",
                "message": "Booking not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = BookingSerializer(
        booking,
        context={"request": request},
    )

    return Response(
        {
            "status": "success",
            "booking": serializer.data,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def worker_update_booking_status_api(request, booking_id):

    worker = get_object_or_404(
        Worker,
        user=request.user,
    )

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        worker=worker,
    )

    serializer = WorkerBookingStatusSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    action = serializer.validated_data["action"]

    # -----------------------------------------
    # ACCEPT BOOKING
    # -----------------------------------------

    if action == "accept":

        if booking.status != "Pending":
            return Response(
                {
                    "detail": "This booking is no longer pending."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "Accepted"

        booking.save(
            update_fields=["status"]
        )

        create_notification(
            recipient=booking.customer,
            booking=booking,
            notification_type="accepted",
            message=(
                f"{worker.name} accepted your booking. "
                f"You can now make an offer."
            ),
        )

        return Response(
            {
                "status": "success",
                "message": "Booking accepted. Customer can now make an offer.",
                "booking": BookingSerializer(
                    booking,
                    context={"request": request},
                ).data,
            },
            status=status.HTTP_200_OK,
        )
    # -----------------------------------------
    # COMPLETE WORK
    # -----------------------------------------

    if action == "complete":

        if booking.status != "Accepted":
            return Response(
                {
                    "detail": "This booking is not active."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.negotiation_status != "Accepted":
            return Response(
                {
                    "detail": (
                        "You can complete the work only after the "
                        "negotiation is completed and the booking is "
                        "finally confirmed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.final_amount is None:
            return Response(
                {
                    "detail": (
                        "Final amount is not available. "
                        "The booking cannot be completed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "Completed"

        booking.save(
            update_fields=["status"]
        )

        create_notification(
            recipient=booking.customer,
            booking=booking,
            notification_type="completed",
            message=(
                f"{worker.name} marked your work as completed."
            ),
        )

        return Response(
            {
                "status": "success",
                "message": "Work marked as completed successfully.",
                "booking": BookingSerializer(
                    booking,
                    context={"request": request},
                ).data,
            },
            status=status.HTTP_200_OK,
        )
    
    # -----------------------------------------
    # REJECT BOOKING
    # -----------------------------------------

    if booking.status != "Pending":
        return Response(
            {
                "detail": "This booking cannot be rejected now."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking.status = "Cancelled"

    booking.save(
        update_fields=["status"]
    )

    create_notification(
        recipient=booking.customer,
        booking=booking,
        notification_type="rejected",
        message=(
            f"{worker.name} rejected your booking request."
        ),
    )

    return Response(
        {
            "status": "success",
            "message": "Booking has been cancelled.",
            "booking": BookingSerializer(
                booking,
                context={"request": request},
            ).data,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def customer_make_offer_api(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user,
    )

    if booking.status != "Accepted":
        return Response(
            {"detail": "Negotiation is available only after the worker accepts the booking."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if booking.negotiation_status != "Not Started":
        return Response(
            {"detail": "Negotiation has already started."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if booking.original_amount is None:
        return Response(
            {"detail": "Original amount is not available."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CustomerOfferSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    offer_amount = serializer.validated_data["offer_amount"]

    suggestions = get_customer_offer_suggestions(
        booking.original_amount
    )

    if offer_amount not in suggestions:
        return Response(
            {
                "detail": "Invalid offer amount.",
                "suggestions": suggestions,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking.customer_offer = offer_amount
    booking.negotiation_status = "Customer Offered"
    booking.save(
        update_fields=[
            "customer_offer",
            "negotiation_status",
        ]
    )

    create_notification(
        recipient=booking.worker.user,
        notification_type="offer",
        message=f"Customer made an offer of ₹{offer_amount} for booking #{booking.id}.",
        booking=booking,
    )

    return Response(
        BookingSerializer(booking).data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def worker_respond_offer_api(request, booking_id):
    worker = get_object_or_404(
        Worker,
        user=request.user,
    )

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        worker=worker,
    )

    if booking.negotiation_status != "Customer Offered":
        return Response(
            {"detail": "There is no customer offer awaiting response."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if booking.customer_offer is None:
        return Response(
            {"detail": "Customer offer is not available."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = WorkerOfferResponseSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    action = serializer.validated_data["action"]

    if action == "accept":
        booking.final_amount = booking.customer_offer
        booking.negotiation_status = "Accepted"

        booking.save(
            update_fields=[
                "final_amount",
                "negotiation_status",
            ]
        )

        create_booking_fee(booking)

        create_notification(
            recipient=booking.customer,
            notification_type="accepted",
            message=f"Your offer of ₹{booking.final_amount} was accepted for booking #{booking.id}.",
            booking=booking,
        )

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK,
        )

    counter_amount = serializer.validated_data.get("counter_amount")

    if counter_amount is None:
        return Response(
            {"detail": "counter_amount is required for counter action."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    suggestions = get_worker_counter_suggestions(
        booking.customer_offer
    )

    if counter_amount not in suggestions:
        return Response(
            {
                "detail": "Invalid counter offer amount.",
                "suggestions": suggestions,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking.worker_counter_offer = counter_amount
    booking.negotiation_status = "Worker Countered"

    booking.save(
        update_fields=[
            "worker_counter_offer",
            "negotiation_status",
        ]
    )

    create_notification(
        recipient=booking.customer,
        notification_type="counter_offer",
        message=f"Worker made a counter offer of ₹{counter_amount} for booking #{booking.id}.",
        booking=booking,
    )

    return Response(
        BookingSerializer(booking).data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def customer_respond_counter_api(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user,
    )

    if booking.negotiation_status != "Worker Countered":
        return Response(
            {"detail": "There is no worker counter offer awaiting response."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if booking.worker_counter_offer is None:
        return Response(
            {"detail": "Worker counter offer is not available."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CustomerCounterResponseSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    action = serializer.validated_data["action"]

    if action == "accept":
        booking.final_amount = booking.worker_counter_offer
        booking.negotiation_status = "Accepted"

        booking.save(
            update_fields=[
                "final_amount",
                "negotiation_status",
            ]
        )

        create_booking_fee(booking)

        create_notification(
            recipient=booking.worker.user,
            notification_type="accepted",
            message=f"Customer accepted your counter offer of ₹{booking.final_amount} for booking #{booking.id}.",
            booking=booking,
        )

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK,
        )

    booking.negotiation_status = "Rejected"
    booking.status = "Cancelled"

    booking.save(
        update_fields=[
            "negotiation_status",
            "status",
        ]
    )

    create_notification(
        recipient=booking.worker.user,
        notification_type="rejected",
        message=f"Customer rejected the counter offer for booking #{booking.id}.",
        booking=booking,
    )

    return Response(
        BookingSerializer(booking).data,
        status=status.HTTP_200_OK,
    )

# =========================================================
# MODULE 5 — REVIEW & RATING API
# =========================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_review_api(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user,
    )

    # -----------------------------------------
    # REVIEW ONLY AFTER COMPLETION
    # -----------------------------------------

    if booking.status != "Completed":
        return Response(
            {
                "detail": "You can review only after the work is completed."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------
    # ONE REVIEW PER BOOKING
    # -----------------------------------------

    if hasattr(booking, "review"):
        return Response(
            {
                "detail": "You have already reviewed this booking."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ReviewCreateSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------
    # CREATE REVIEW
    # -----------------------------------------

    review = Review.objects.create(
        booking=booking,
        worker=booking.worker,
        customer=request.user,
        rating=serializer.validated_data["rating"],
        comment=serializer.validated_data.get("comment", ""),
    )

    # -----------------------------------------
    # UPDATE WORKER RATING
    # Same logic as existing Web flow
    # -----------------------------------------

    worker = booking.worker

    avg_rating = (
        worker.worker_reviews.aggregate(
            Avg("rating")
        )["rating__avg"]
    )

    worker.rating = round(avg_rating, 1)
    worker.reviews = worker.worker_reviews.count()

    worker.save(
        update_fields=[
            "rating",
            "reviews",
        ]
    )
    
    # -----------------------------------------
    # NOTIFY WORKER ABOUT NEW REVIEW
    # -----------------------------------------

    create_notification(
        recipient=worker.user,
        booking=booking,
        notification_type="review",
        message=(
            f"{request.user.get_full_name() or request.user.username} "
            f"submitted a {review.rating}-star review for booking #{booking.id}."
        ),
    )

    # -----------------------------------------
    # RESPONSE
    # -----------------------------------------

    return Response(
        {
            "status": "success",
            "message": "Thank you! Your review has been submitted.",
            "review": {
                "id": review.id,
                "booking_id": review.booking_id,
                "worker_id": review.worker_id,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at,
            },
            "worker": {
                "id": worker.id,
                "name": worker.name,
                "rating": worker.rating,
                "reviews": worker.reviews,
            },
        },
        status=status.HTTP_201_CREATED,
    )

# =========================================================
# MODULE 8 — NOTIFICATIONS API
# =========================================================


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """
    Return notifications belonging only to the
    authenticated user.
    """

    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("booking")
        .order_by("-created_at")
    )

    serializer = NotificationSerializer(
        notifications,
        many=True
    )

    return Response(
        {
            "status": "success",
            "count": notifications.count(),
            "results": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def notification_unread_count(request):
    """
    Return unread notification count for the
    authenticated user only.
    """

    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return Response(
        {
            "status": "success",
            "unread_count": unread_count,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def notification_mark_read(
    request,
    notification_id
):
    """
    Mark one notification as read.

    The notification must belong to the
    authenticated user.
    """

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    if not notification.is_read:

        notification.is_read = True

        notification.save(
            update_fields=["is_read"]
        )

    return Response(
        {
            "status": "success",
            "message": "Notification marked as read.",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def notification_mark_all_read(request):
    """
    Mark all unread notifications belonging to
    the authenticated user as read.
    """

    updated_count = (
        Notification.objects
        .filter(
            recipient=request.user,
            is_read=False
        )
        .update(is_read=True)
    )

    return Response(
        {
            "status": "success",
            "message": "All notifications marked as read.",
            "updated_count": updated_count,
        },
        status=status.HTTP_200_OK,
    )

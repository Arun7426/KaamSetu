from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db import models
from django.utils import timezone

from .models import WorkerLedger, FeeSetting, Promotion
from .alert_service import check_worker_payment_alert



def get_fee_setting():
    """
    Get the active platform fee setting.
    If no setting exists, create the default ₹20 fixed fee.
    """

    setting = FeeSetting.objects.first()

    # Create the default only when no FeeSetting exists at all.
    # If Super Admin intentionally sets the existing setting inactive,
    # keep it inactive so the platform fee is not recreated as active.
    if setting is None:
        setting = FeeSetting.objects.create(
            fee_type="fixed",
            fee_value=Decimal("20.00"),
            is_active=True
        )

    return setting


def get_active_promotion():
    """
    Return the currently active promotion.
    """

    return Promotion.objects.filter(
        is_active=True
    ).order_by(
        "-created_at"
    ).first()


def calculate_platform_fee(booking):
    """
    Calculate the platform fee for a final accepted booking.
    """

    setting = get_fee_setting()

    if not setting.is_active:
        return Decimal("0.00")

    if setting.fee_type == "fixed":
        return setting.fee_value

    if setting.fee_type == "percentage":

        if not booking.final_amount:
            return Decimal("0.00")

        fee = (
            Decimal(booking.final_amount)
            * setting.fee_value
            / Decimal("100")
        )

        return fee.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    return Decimal("0.00")


@transaction.atomic
def create_booking_fee(booking):
    """
    Create the KaamSetu platform fee after final acceptance.

    Active promotion can waive the fee for the first
    N final accepted bookings of each worker.
    """

    # -----------------------------------------
    # Prevent duplicate fee for same booking
    # -----------------------------------------

    existing_entry = WorkerLedger.objects.filter(
        booking=booking,
        transaction_type="Booking Fee"
    ).first()

    if existing_entry:
        return existing_entry


    # -----------------------------------------
    # Check active promotion
    # -----------------------------------------

    promotion = get_active_promotion()

    if promotion:

        successful_bookings = booking.__class__.objects.filter(
            worker=booking.worker,
            negotiation_status="Accepted"
        ).exclude(
            id=booking.id
        ).count()

        if successful_bookings < promotion.free_bookings_limit:

            return None


    # -----------------------------------------
    # Calculate actual platform fee
    # -----------------------------------------

    fee_amount = calculate_platform_fee(
        booking
    )

    if fee_amount <= 0:
        return None


    # -----------------------------------------
    # Create ledger entry
    # -----------------------------------------

    ledger_entry = WorkerLedger.objects.create(
        worker=booking.worker,
        booking=booking,
        transaction_type="Booking Fee",
        amount=fee_amount,
        status="Pending",
        description="KaamSetu platform booking fee"
    )

    # -----------------------------------------
    # PAYMENT ALERT CHECK
    # -----------------------------------------

    check_worker_payment_alert(
        booking.worker
    )

    return ledger_entry


def get_worker_outstanding(worker):
    """
    Return the worker's current unpaid platform fee.
    """

    outstanding = WorkerLedger.objects.filter(
        worker=worker,
        transaction_type="Booking Fee",
        status="Pending"
    ).aggregate(
        total=models.Sum("amount")
    )["total"]

    return outstanding or Decimal("0.00")

BOOKING_BLOCK_LIMIT = Decimal("200.00")


def can_worker_receive_booking(worker):
    """
    Check whether the worker is allowed to receive new bookings.
    """

    outstanding = get_worker_outstanding(worker)

    return outstanding < BOOKING_BLOCK_LIMIT

@transaction.atomic
def settle_worker_payment(worker, amount):
    """
    Settle the worker's outstanding platform fees.

    Payment is applied to the oldest pending booking fees first.
    """

    amount = Decimal(amount)

    if amount <= 0:
        return False

    pending_entries = WorkerLedger.objects.filter(
        worker=worker,
        transaction_type="Booking Fee",
        status="Pending"
    ).order_by(
        "created_at"
    )

    remaining_amount = amount

    for entry in pending_entries:

        if remaining_amount <= 0:
            break

        if remaining_amount >= entry.amount:

            remaining_amount -= entry.amount

            entry.status = "Paid"
            entry.paid_at = timezone.now()

            entry.save(
                update_fields=[
                    "status",
                    "paid_at"
                ]
            )

        else:
            # Partial payment will be handled later
            break
        # -----------------------------------------
        # PAYMENT ALERT CHECK
        # -----------------------------------------

        check_worker_payment_alert(
            worker
        )

        return True

import razorpay
from django.conf import settings


def get_razorpay_client():
    """
    Return configured Razorpay client.
    """

    if not settings.RAZORPAY_KEY_ID:
        raise ValueError("Razorpay Key ID is not configured.")

    if not settings.RAZORPAY_KEY_SECRET:
        raise ValueError("Razorpay Key Secret is not configured.")

    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

def create_razorpay_order(worker, amount, transaction):
    """
    Create a Razorpay order for a worker payment transaction.
    """

    client = get_razorpay_client()

    amount = Decimal(amount)

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    razorpay_order = client.order.create({
        "amount": int(amount * Decimal("100")),
        "currency": "INR",
        "receipt": f"KS-PAY-{transaction.id}",
    })

    transaction.provider = "Razorpay"
    transaction.provider_order_id = razorpay_order["id"]
    transaction.status = "Pending"

    transaction.save(
        update_fields=[
            "provider",
            "provider_order_id",
            "status",
            "updated_at",
        ]
    )

    return razorpay_order


def verify_razorpay_payment(
    order_id,
    payment_id,
    signature,
    expected_amount,
):
    """
    Verify a successful Razorpay payment server-side.

    Checks:
    1. Razorpay checkout signature.
    2. Payment belongs to the expected order.
    3. Currency is INR.
    4. Razorpay amount exactly matches the server-side transaction amount.
    5. Razorpay payment status is captured.

    This function only verifies the gateway payment. It does not
    settle WorkerLedger; settlement remains a separate operation.
    """

    client = get_razorpay_client()

    expected_amount = Decimal(expected_amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    if expected_amount <= 0:
        raise ValueError(
            "Expected payment amount must be greater than zero."
        )

    # 1. Server-side signature verification
    client.utility.verify_payment_signature({
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    })

    # 2. Fetch the payment directly from Razorpay
    payment = client.payment.fetch(payment_id)

    fetched_order_id = payment.get("order_id")
    fetched_amount = payment.get("amount")
    fetched_currency = payment.get("currency")
    fetched_status = payment.get("status")

    if fetched_order_id != order_id:
        raise ValueError(
            "Razorpay payment does not belong to the expected order."
        )

    if fetched_currency != "INR":
        raise ValueError(
            "Razorpay payment currency does not match INR."
        )

    if fetched_amount is None:
        raise ValueError(
            "Razorpay payment amount is missing."
        )

    # Razorpay stores amount in paise.
    fetched_amount_rupees = (
        Decimal(fetched_amount) / Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    if fetched_amount_rupees != expected_amount:
        raise ValueError(
            "Razorpay payment amount does not match the transaction amount."
        )

    if fetched_status != "captured":
        raise ValueError(
            f"Razorpay payment is not captured. Current status: "
            f"{fetched_status or 'unknown'}."
        )

    return payment

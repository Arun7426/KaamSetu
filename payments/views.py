from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction as db_transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

import razorpay

from .services import (
    get_worker_outstanding,
    create_razorpay_order,
)
from .models import WorkerPaymentTransaction


@login_required
def worker_payment(request):

    # Only workers can access this page
    try:
        worker = request.user.worker_profile
    except ObjectDoesNotExist:
        messages.error(
            request,
            "यह पेज केवल कामगारों के लिए उपलब्ध है।"
        )
        return redirect("home")

    outstanding = get_worker_outstanding(worker)

    # No outstanding payment
    if outstanding <= 0:
        messages.info(
            request,
            "आपका कोई बकाया भुगतान नहीं है।"
        )
        return redirect("worker_dashboard")

    # Default values for first page load
    payment_created = False
    payment_transaction = None
    razorpay_order = None

    if request.method == "POST":

        raw_amount = request.POST.get("payment_amount")

        # Validate entered amount
        try:
            payment_amount = Decimal(raw_amount).quantize(
                Decimal("0.01")
            )
        except (InvalidOperation, TypeError, AttributeError):
            messages.error(
                request,
                "कृपया सही भुगतान राशि दर्ज करें।"
            )
            return redirect("worker_payment")

        # Amount must be greater than zero
        if payment_amount <= Decimal("0.00"):
            messages.error(
                request,
                "भुगतान राशि ₹0 से अधिक होनी चाहिए।"
            )
            return redirect("worker_payment")

        # Cannot pay more than current outstanding
        if payment_amount > outstanding:
            messages.error(
                request,
                f"भुगतान राशि ₹{outstanding} से अधिक नहीं हो सकती।"
            )
            return redirect("worker_payment")

        # Create transaction for selected amount
        payment_transaction = WorkerPaymentTransaction.objects.create(
            worker=worker,
            amount=payment_amount,
            status="Created",
            provider="Razorpay"
        )

        # Create Razorpay order for selected amount
        razorpay_order = create_razorpay_order(
            worker=worker,
            amount=payment_amount,
            transaction=payment_transaction
        )

        payment_created = True

    return render(
        request,
        "payments/worker_payment.html",
        {
            "worker": worker,
            "outstanding": outstanding,
            "payment_created": payment_created,
            "razorpay_amount": (
                int(payment_transaction.amount * Decimal("100"))
                if payment_transaction
                else 0
            ),
            "payment_transaction": payment_transaction,
            "razorpay_order": razorpay_order,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        }
    )


@login_required
@require_POST
def worker_payment_verify(request):

    # Only workers can access this page
    try:
        worker = request.user.worker_profile
    except ObjectDoesNotExist:
        return render(
            request,
            "payments/worker_payment.html",
            {
                "error": "यह पेज केवल कामगारों के लिए उपलब्ध है।"
            },
            status=403,
        )

    transaction_id = request.POST.get("transaction_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    if not all([
        transaction_id,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ]):
        messages.error(
            request,
            "Payment verification details incomplete हैं।"
        )
        return redirect("worker_payment")

    try:

        with db_transaction.atomic():

            payment_transaction = (
                WorkerPaymentTransaction.objects
                .select_for_update()
                .get(
                    id=transaction_id,
                    worker=worker,
                )
            )

            # Idempotency
            if payment_transaction.status == "Verified":
                messages.success(
                    request,
                    "यह payment पहले ही verify हो चुका है।"
                )
                return redirect("worker_dashboard")

            # Verify correct Razorpay order
            if payment_transaction.provider_order_id != razorpay_order_id:
                messages.error(
                    request,
                    "Invalid Razorpay order."
                )
                return redirect("worker_payment")

            # Only pending transaction can be verified
            if payment_transaction.status != "Pending":
                messages.error(
                    request,
                    "यह payment verification के लिए valid नहीं है।"
                )
                return redirect("worker_payment")

            client = razorpay.Client(
                auth=(
                    settings.RAZORPAY_KEY_ID,
                    settings.RAZORPAY_KEY_SECRET,
                )
            )

            try:
                client.utility.verify_payment_signature({
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                })

            except razorpay.errors.SignatureVerificationError:

                payment_transaction.status = "Failed"
                payment_transaction.save(
                    update_fields=["status"]
                )

                messages.error(
                    request,
                    "Payment signature verification failed."
                )

                return redirect("worker_payment")

            payment_transaction.provider_payment_id = (
                razorpay_payment_id
            )

            payment_transaction.status = "Verified"

            payment_transaction.save(
                update_fields=[
                    "provider_payment_id",
                    "status",
                ]
            )

        messages.success(
            request,
            "Payment successfully verified."
        )

        return redirect("worker_dashboard")

    except WorkerPaymentTransaction.DoesNotExist:

        messages.error(
            request,
            "Payment transaction नहीं मिली।"
        )

        return redirect("worker_payment")
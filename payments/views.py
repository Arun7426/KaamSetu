from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from .services import (
    get_worker_outstanding,
    settle_worker_payment,
)


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

    if request.method == "POST":

        settle_worker_payment(
            worker,
            outstanding
        )

        messages.success(
            request,
            "आपका KaamSetu भुगतान सफलतापूर्वक पूरा हो गया है।"
        )

        return redirect("worker_dashboard")

    return render(
        request,
        "payments/worker_payment.html",
        {
            "worker": worker,
            "outstanding": outstanding,
        }
    )
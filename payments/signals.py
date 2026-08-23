from django.db.models.signals import post_save
from django.dispatch import receiver

from payments.models import WorkerLedger
from payments.alert_service import check_worker_payment_alert


@receiver(post_save, sender=WorkerLedger)
def worker_ledger_created(
    sender,
    instance,
    created,
    **kwargs
):

    # Only new ledger entries
    if not created:
        return

    # Only Booking Fee entries
    if instance.transaction_type != "Booking Fee":
        return

    # Only pending fees contribute to outstanding
    if instance.status != "Pending":
        return

    check_worker_payment_alert(
        instance.worker
    )
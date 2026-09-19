from django.urls import path

from . import views


urlpatterns = [

    path(
        "worker-payment/",
        views.worker_payment,
        name="worker_payment"
    ),

    path(
        "worker-payment/verify/",
        views.worker_payment_verify,
        name="worker_payment_verify"
    ),

]
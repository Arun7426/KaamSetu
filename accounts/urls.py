from django.urls import path
from . import views

urlpatterns = [

    path(
        "register/",
        views.choose_role,
        name="register",
    ),

    path(
        "register/customer/",
        views.register,
        name="customer_register",
    ),

    path(
        "login/",
        views.user_login,
        name="login",
    ),

    path(
        "logout/",
        views.user_logout,
        name="logout",
    ),

    path(
        "dashboard/",
        views.customer_dashboard,
        name="customer_dashboard",
    ),

    path(
            "customer/edit-profile/",
            views.edit_customer_profile,
            name="edit_customer_profile",
        ),
        
    path(
        "customer/update-location/",
        views.update_customer_location,
        name="update_customer_location",
    ),

    
]

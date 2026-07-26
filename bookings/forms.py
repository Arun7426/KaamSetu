from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):

    class Meta:

        model = Booking

        fields = [
            "customer_name",
            "customer_mobile",
            "customer_address",
            "work_date",
            "work_description",
        ]

        widgets = {

            "customer_name":
                forms.TextInput(attrs={"class":"form-control"}),

            "customer_mobile":
                forms.TextInput(attrs={"class":"form-control"}),

            "customer_address":
                forms.Textarea(attrs={"class":"form-control"}),

            "work_date":
                forms.DateInput(
                    attrs={
                        "type":"date",
                        "class":"form-control"
                    }
                ),

            "work_description":
                forms.Textarea(attrs={"class":"form-control"}),

        }
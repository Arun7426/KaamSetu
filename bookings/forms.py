from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):

    class Meta:

        model = Booking

        fields = [
            "customer_address",
            "work_date",
            "work_description",
        ]

        widgets = {

            "customer_address":
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 3,
                        "placeholder": "पूरा पता लिखें जहाँ काम करवाना है"
                    }
                ),

            "work_date":
                forms.DateInput(
                    attrs={
                        "type": "date",
                        "class": "form-control"
                    }
                ),

            "work_description":
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 4,
                        "placeholder": "काम का विवरण लिखें..."
                    }
                ),
        }
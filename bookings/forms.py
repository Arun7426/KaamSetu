from django import forms
from .models import Booking, Review


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

class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review

        fields = [
            "rating",
            "title",
            "comment",
        ]

        widgets = {

            "rating": forms.Select(
                choices=[
                    (5, "⭐⭐⭐⭐⭐ Excellent"),
                    (4, "⭐⭐⭐⭐ Very Good"),
                    (3, "⭐⭐⭐ Good"),
                    (2, "⭐⭐ Average"),
                    (1, "⭐ Poor"),
                ],
                attrs={
                    "class": "form-control"
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Review Title"
                }
            ),

            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Share your experience with this worker..."
                }
            ),
        }
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomerProfile
from .location import distance_km, nearby_workers
from .models import Worker


class LocationTests(TestCase):
    def make_worker(self, **overrides):
        values = {
            "name": "Ravi",
            "mobile": "9876543210",
            "profession": "Plumber",
            "experience": 4,
            "city": "Delhi",
            "area": "Central",
            "daily_wage": Decimal("800.00"),
            "latitude": Decimal("28.613900"),
            "longitude": Decimal("77.209000"),
            "work_range": Decimal("10.00"),
        }
        values.update(overrides)
        return Worker.objects.create(**values)

    def test_distance_and_range_filter_include_only_serving_workers(self):
        nearby = self.make_worker()
        far_away = self.make_worker(
            mobile="9876543211", latitude=Decimal("28.900000"), longitude=Decimal("77.209000")
        )

        results = nearby_workers(Worker.objects.all(), (Decimal("28.613900"), Decimal("77.209000")))

        self.assertEqual([worker.id for worker in results], [nearby.id])
        self.assertEqual(results[0].distance_km, 0.0)
        self.assertGreater(distance_km(28.6139, 77.209, far_away.latitude, far_away.longitude), 10)

    def test_customer_location_is_saved(self):
        user = User.objects.create_user("customer", password="pass")
        profile = CustomerProfile.objects.create(user=user, mobile="9876543212")
        self.client.force_login(user)

        response = self.client.post(reverse("update_customer_location"), {"latitude": "28.6139", "longitude": "77.2090"})

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.latitude, Decimal("28.613900"))
        self.assertEqual(profile.longitude, Decimal("77.209000"))

    def test_worker_location_rejects_non_finite_coordinates(self):
        user = User.objects.create_user("worker", password="pass")
        worker = self.make_worker(user=user)
        self.client.force_login(user)

        response = self.client.post(reverse("update_worker_location"), {"latitude": "NaN", "longitude": "77.2090"})

        self.assertEqual(response.status_code, 400)
        worker.refresh_from_db()
        self.assertEqual(worker.latitude, Decimal("28.613900"))

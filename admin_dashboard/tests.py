from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomerProfile
from workers.models import Worker

from .models import AuditLog


class FraudControlTests(TestCase):

    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username="superadmin",
            password="StrongPass123!"
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="StrongPass123!"
        )
        self.admin.is_staff = True
        self.admin.save(update_fields=["is_staff"])

        self.worker_user = User.objects.create_user(
            username="worker1",
            password="StrongPass123!"
        )

        self.worker = Worker.objects.create(
            user=self.worker_user,
            name="Test Worker",
            mobile="9999999999",
            profession="Plumber",
            experience=5,
            city="Delhi",
            area="Test Area",
            daily_wage="800.00",
        )

        self.customer = User.objects.create_user(
            username="customer1",
            password="StrongPass123!"
        )
        CustomerProfile.objects.create(
            user=self.customer,
            mobile="8888888888",
        )

    def login_super_admin(self):
        self.client.force_login(self.super_admin)

    def test_fraud_control_is_super_admin_only(self):
        response = self.client.get(reverse("admin_fraud_control"))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_fraud_control"))
        self.assertEqual(response.status_code, 403)

    def test_super_admin_can_block_and_unblock_worker(self):
        self.login_super_admin()

        response = self.client.post(
            reverse(
                "admin_toggle_worker_block",
                args=[self.worker.id]
            )
        )

        self.assertRedirects(
            response,
            reverse("admin_fraud_control")
        )

        self.worker_user.refresh_from_db()
        self.assertFalse(self.worker_user.is_active)

        self.assertTrue(
            AuditLog.objects.filter(
                module="Fraud Control",
                action="UPDATE",
                target_id=str(self.worker.id),
            ).exists()
        )

        response = self.client.post(
            reverse(
                "admin_toggle_worker_block",
                args=[self.worker.id]
            )
        )

        self.assertRedirects(
            response,
            reverse("admin_fraud_control")
        )

        self.worker_user.refresh_from_db()
        self.assertTrue(self.worker_user.is_active)

    def test_blocked_customer_cannot_login(self):
        self.login_super_admin()

        self.client.post(
            reverse(
                "admin_toggle_customer_block",
                args=[self.customer.id]
            )
        )

        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_active)

        response = self.client.post(
            reverse("login"),
            {
                "username": "customer1",
                "password": "StrongPass123!",
                "role": "customer",
            }
        )

        self.assertContains(
            response,
            "Invalid Username or Password"
        )

    def test_super_admin_can_delete_customer_with_audit_log(self):
        self.login_super_admin()

        customer_id = self.customer.id

        response = self.client.post(
            reverse(
                "admin_delete_customer",
                args=[customer_id]
            )
        )

        self.assertRedirects(
            response,
            reverse("admin_fraud_control")
        )

        self.assertFalse(
            User.objects.filter(id=customer_id).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                module="Fraud Control",
                action="DELETE",
                target_id=str(customer_id),
            ).exists()
        )

    def test_super_admin_can_delete_worker_and_linked_user(self):
        self.login_super_admin()

        worker_id = self.worker.id
        user_id = self.worker_user.id

        response = self.client.post(
            reverse(
                "admin_delete_worker",
                args=[worker_id]
            )
        )

        self.assertRedirects(
            response,
            reverse("admin_fraud_control")
        )

        self.assertFalse(
            Worker.objects.filter(id=worker_id).exists()
        )
        self.assertFalse(
            User.objects.filter(id=user_id).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                module="Fraud Control",
                action="DELETE",
                target_id=str(worker_id),
            ).exists()
        )

    def test_normal_admin_cannot_perform_fraud_actions(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "admin_toggle_customer_block",
                args=[self.customer.id]
            )
        )

        self.assertEqual(response.status_code, 403)

        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_active)

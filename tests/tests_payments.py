from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from payments.models import Payment
from payments.serializers import PaymentSerializer, PaymentDetailSerializer
from tests.tests_borrowings import sample_borrowing, sample_user

PAYMENT_URL = reverse("payments:payment-list")


def detail_url(book_id):
    return reverse("payment:payment-detail", args=(book_id,))


def sample_payment(user=None) -> Payment:
    if not user:
        user = sample_user()
    borrowing = sample_borrowing(user=user)
    defaults = {
        "payment_status": Payment.PaymentStatus.PENDING,
        "payment_type": Payment.PaymentType.BORROWING_PAYMENT,
        "borrowing": borrowing,
        "session_url": "test_url",
        "session_id": "test_session_id",
        "amount_to_pay": Decimal("9.99"),
    }
    return Payment.objects.create(**defaults)


class UnauthenticatedPaymentTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_payment_list(self) -> None:
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payment_detail(self) -> None:
        payment_id = 1
        url = detail_url(payment_id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class CustomerPaymentTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="customer@email.com",
            password="1qazcde3",
            is_staff=False,
        )
        self.client.force_authenticate(self.user)

    def test_payments_list(self) -> None:
        payment_sample_user = sample_payment()
        payment_self_user = sample_payment(self.user)

        res = self.client.get(PAYMENT_URL)

        payments_all = Payment.objects.all()
        payments_self_user = Payment.objects.filter(
            borrowing__user=payment_self_user.borrowing.user
        )

        serializer = PaymentSerializer(payments_self_user, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check non-staff users can view only their own payments
        self.assertNotEqual(res.data.get("count"), payments_all.count())
        self.assertEqual(res.data.get("results"), serializer.data)

    def test_payment_detail(self) -> None:
        payment_self_user = sample_payment(user=self.user)
        url = detail_url(payment_self_user.id)

        res = self.client.get(url)

        serializer = PaymentDetailSerializer(payment_self_user)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_payment_post_patch_put_not_allowed(self) -> None:
        res_post = self.client.post(PAYMENT_URL)
        res_patch = self.client.patch(PAYMENT_URL)
        res_put = self.client.put(PAYMENT_URL)

        self.assertEqual(res_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(res_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(res_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

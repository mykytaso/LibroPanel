from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingDetailSerializer
from tests.tests_books import sample_book

BORROWING_URL = reverse("borrowing:borrowing-list")


def detail_url(book_id):
    return reverse("borrowing:borrowing-detail", args=(book_id,))


def sample_user(**params):
    defaults = {
        "email": "sample_user@mail.com",
        "password": "1qazcde3",
        "is_staff": False,
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


def sample_borrowing(**params):
    user = params.get("user")
    if not user:
        user = sample_user()

    book = params.get("book")
    if not book:
        book = sample_book()

    defaults = {
        "user": user,
        "book": book,
        "borrow_date": date(2024, 11, 1),
        "expected_return_date": date(2024, 11, 3),
        "actual_return_date": None,
        "is_active": True,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


class UnauthenticatedBorrowingTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_borrowings_list(self) -> None:
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_borrowing_detail(self) -> None:
        borrowing_id = 1
        url = detail_url(borrowing_id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class CustomerBorrowingsTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="customer@email.com",
            password="1qazcde3",
            is_staff=False,
        )
        self.client.force_authenticate(self.user)

    def test_borrowings_list(self) -> None:
        borrowing_sample_user = sample_borrowing()
        borrowing_self_user = sample_borrowing(user=self.user)

        res = self.client.get(BORROWING_URL)

        borrowings_all = Borrowing.objects.all()
        borrowings_self_user = Borrowing.objects.filter(user=borrowing_self_user.user)

        serializer = BorrowingSerializer(borrowings_self_user, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check non-staff users can view only their own borrowings
        self.assertNotEqual(res.data.get("count"), borrowings_all.count())
        self.assertEqual(res.data.get("results"), serializer.data)

    def test_borrowing_list_filter_is_active(self) -> None:
        borrowing_is_active_true = sample_borrowing(is_active=True, user=self.user)
        borrowing_is_active_false = sample_borrowing(is_active=False, user=self.user)

        res = self.client.get(
            BORROWING_URL,
            {"is_active": "true"},
        )

        serializer_borrowing_is_active_true = BorrowingSerializer(
            borrowing_is_active_true
        )
        serializer_borrowing_is_active_false = BorrowingSerializer(
            borrowing_is_active_false
        )

        self.assertIn(
            serializer_borrowing_is_active_true.data,
            res.data.get("results"),
        )
        self.assertNotIn(
            serializer_borrowing_is_active_false.data,
            res.data.get("results"),
        )

    def test_borrowing_detail(self) -> None:
        borrowing_self_user = sample_borrowing(user=self.user)
        url = detail_url(borrowing_self_user.id)

        res = self.client.get(url)

        serializer = BorrowingDetailSerializer(borrowing_self_user)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_borrowing_create(self) -> None:
        book = sample_book()
        payload = {
            "user": self.user.id,
            "book": book.id,
            "borrow_date": date(2024, 11, 1),
            "expected_return_date": date(2024, 11, 3),
            "actual_return_date": date(2024, 11, 3),
            "is_active": True,
        }

        res = self.client.post(BORROWING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data.get("detail"), "Borrowing created successfully")
        self.assertIn(
            "https://checkout.stripe.com/c/pay/", res.data.get("stripe_session_url")
        )

    def test_borrowing_update_not_allowed(self) -> None:
        borrowing = sample_borrowing()
        url = detail_url(borrowing.id)
        res = self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_borrowing_delete_not_allowed(self) -> None:
        borrowing = sample_borrowing()
        url = detail_url(borrowing.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_borrowing_str_method(self):
        borrowing = sample_borrowing()
        self.assertEqual(
            str(borrowing),
            f"On {borrowing.borrow_date} {borrowing.user} borrowed {borrowing.book}. "
            f"Expected return date: {borrowing.expected_return_date}.",
        )


class AdminBorrowingTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="customer@email.com",
            password="1qazcde3",
            is_staff=False,
        )
        self.client.force_authenticate(self.user)

    def test_borrowing_list_filter_user_id(self) -> None:
        borrowing_self_user = sample_borrowing(user=self.user)
        borrowing_sample_user = sample_borrowing()

        res = self.client.get(
            BORROWING_URL,
            {"user_id": self.user.id},
        )

        serializer_borrowing_user_id_self = BorrowingSerializer(borrowing_self_user)
        serializer_borrowing_user_id_sample = BorrowingSerializer(borrowing_sample_user)

        self.assertIn(
            serializer_borrowing_user_id_self.data,
            res.data.get("results"),
        )
        self.assertNotIn(
            serializer_borrowing_user_id_sample.data,
            res.data.get("results"),
        )

    def test_borrowing_delete_not_allowed(self) -> None:
        borrowing = sample_borrowing()
        url = detail_url(borrowing.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

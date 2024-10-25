from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book

BORROWING_URL = reverse("borrowing:borrowing-list")


class UnauthenticatedBorrowingsTests(TestCase):
    def test_borrowings_list(self) -> None:
        res = self.client.get(BORROWING_URL)
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
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_borrowing(self) -> None:
        book = Book.objects.create(
            title="Test_book_title",
            author="Test_book_author",
            cover=Book.CoverChoices.HARD,
            copies=3,
            daily_fee=Decimal("0.99"),
        )

        payload = {
            "user": self.user.id,
            "book": book.id,
            "borrow_date": date(2024, 11, 1),
            "expected_return_date": date(2024, 11, 4),
            "is_active": True,
        }
        res = self.client.post(BORROWING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

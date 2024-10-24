from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book

BOOK_URL = reverse("books:book-list")


def detail_url(book_id):
    return reverse("books:book-detail", args=(book_id,))


def sample_book(**params) -> Book:
    defaults = {
        "title": "Test_book_title",
        "author": "Test_book_author",
        "cover": Book.CoverChoices.HARD,
        "copies": 3,
        "daily_fee": Decimal("0.99"),
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


class UnauthenticatedBookTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_not_required(self):
        res = self.client.get(BOOK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_book_not_allowed_for_unauthorized(self):
        payload = {
            "title": "Test_book_title",
            "author": "Test_book_author",
            "cover": Book.CoverChoices.HARD,
            "copies": 3,
            "daily_fee": Decimal("0.99"),
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class CustomerBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="customer@email.com",
            password="1qazcde3",
            is_staff=False,
        )
        self.client.force_authenticate(self.user)

    def test_create_book_not_allowed_for_customers(self):
        payload = {
            "title": "Test_book_title",
            "author": "Test_book_author",
            "cover": Book.CoverChoices.HARD,
            "copies": 3,
            "daily_fee": Decimal("0.99"),
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_book_not_allowed_for_customers(self):
        book = sample_book()
        url = detail_url(book.id)

        updated_payload = {
            "title": "Updated Book Title",
            "author": "Updated Book Author",
            "cover": Book.CoverChoices.SOFT,
            "copies": 10,
            "daily_fee": Decimal("2.99"),
        }

        response = self.client.patch(url, updated_payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@email.com",
            password="1qazcde3",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_book_allowed_for_staff(self):
        payload = {
            "title": "Test_book_title",
            "author": "Test_book_author",
            "cover": Book.CoverChoices.HARD,
            "copies": 3,
            "daily_fee": Decimal("0.99"),
        }
        res = self.client.post(BOOK_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_book_allowed_for_staff(self):
        book = sample_book()
        url = detail_url(book.id)

        updated_payload = {
            "title": "Updated Book Title",
            "author": "Updated Book Author",
            "cover": Book.CoverChoices.SOFT,
            "copies": 10,
            "daily_fee": Decimal("2.99"),
        }

        response = self.client.patch(url, updated_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        book.refresh_from_db()

        self.assertEqual(book.title, updated_payload["title"])
        self.assertEqual(book.author, updated_payload["author"])
        self.assertEqual(book.cover, updated_payload["cover"])
        self.assertEqual(book.copies, updated_payload["copies"])
        self.assertEqual(book.daily_fee, updated_payload["daily_fee"])

    def test_delete_book_not_allowed_for_staff(self):
        book = sample_book()
        url = detail_url(book.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

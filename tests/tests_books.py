from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer, BookListSerializer

BOOK_URL = reverse("books:book-list")
PAYLOAD_01 = {
    "title": "Test_book_title",
    "author": "Test_book_author",
    "cover": Book.CoverChoices.HARD,
    "copies": 3,
    "daily_fee": Decimal("0.99"),
}
PAYLOAD_02 = {
    "title": "Updated Book Title",
    "author": "Updated Book Author",
    "cover": Book.CoverChoices.SOFT,
    "copies": 10,
    "daily_fee": Decimal("2.99"),
}


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

    def test_books_list(self):
        sample_book()
        res = self.client.get(BOOK_URL)

        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("results"), serializer.data)

    def test_book_detail(self):
        book = sample_book()
        url = detail_url(book.id)

        res = self.client.get(url)

        serializer = BookSerializer(book)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_book_create_not_allowed_for_unauthorized(self):
        res = self.client.post(BOOK_URL, PAYLOAD_01)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class CustomerBookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="customer@email.com",
            password="1qazcde3",
            is_staff=False,
        )
        self.client.force_authenticate(self.user)

    def test_book_create_not_allowed_for_customers(self):
        res = self.client.post(BOOK_URL, PAYLOAD_01)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_book_update_not_allowed_for_customers(self):
        url = detail_url(sample_book().id)

        res = self.client.patch(url, PAYLOAD_02)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@email.com",
            password="1qazcde3",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_book_create_allowed_for_staff(self):
        res = self.client.post(BOOK_URL, PAYLOAD_01)
        book = Book.objects.get(pk=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in PAYLOAD_01:
            self.assertEqual(getattr(book, key), PAYLOAD_01[key])

    def test_book_update_allowed_for_staff(self):
        res = self.client.post(BOOK_URL, PAYLOAD_01)
        book = Book.objects.get(pk=res.data["id"])
        res_updated = self.client.patch(detail_url(book.id), PAYLOAD_02)

        book.refresh_from_db()

        self.assertEqual(res_updated.status_code, status.HTTP_200_OK)
        for key in PAYLOAD_02:
            self.assertEqual(getattr(book, key), PAYLOAD_02[key])

    def test_book_delete_not_allowed_for_staff(self):
        book = sample_book()
        url = detail_url(book.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_book_str_method(self):
        book = Book.objects.create(**PAYLOAD_01)
        self.assertEqual(str(book), "Title: Test_book_title, Author: Test_book_author")

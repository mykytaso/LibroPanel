from django.db import models

from books.models import Book
from users.models import User


class Borrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return (
            f"On {self.borrow_date} {self.user} borrowed {self.book}. "
            f"Expected return date: {self.expected_return_date}."
        )

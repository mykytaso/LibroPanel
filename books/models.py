from django.db import models
from django.db.models import UniqueConstraint


class Book(models.Model):

    class CoverChoices(models.TextChoices):
        HARD = "Hard"
        SOFT = "Soft"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=50, choices=CoverChoices.choices)
    copies = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["title", "author"],
                name="unique_title_and_author",
            ),
        ]

    def borrow_one_copy(self) -> None:
        self.copies -= 1

    def return_one_copy(self) -> None:
        self.copies += 1

    def __str__(self):
        return f"Title: {self.title}, Author: {self.author}"

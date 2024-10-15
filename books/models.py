from django.db import models


class Book(models.Model):

    class CoverChoices(models.TextChoices):
        HARD = "Hard"
        SOFT = "Soft"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=50, choices=CoverChoices.choices)
    copies = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def borrow_one_copy(self) -> None:
        self.copies -= 1

    def return_one_copy(self) -> None:
        self.copies += 1

    def __str__(self):
        return f"Title: {self.title}, Author: {self.author}"

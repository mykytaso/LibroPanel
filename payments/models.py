from django.db import models
from django.db.models import UniqueConstraint

from borrowings.models import Borrowing


class Payment(models.Model):

    class PaymentStatus(models.TextChoices):
        PENDING = "pending"
        PAID = "paid"
        EXPIRED = "expired"

    class PaymentType(models.TextChoices):
        BORROWING_PAYMENT = "borrowing_payment"
        OVERDUE_FEE_PAYMENT = "overdue_fee_payment"

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.BORROWING_PAYMENT,
    )
    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(max_length=500)
    session_id = models.CharField(max_length=100)
    amount_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["payment_type", "borrowing"],
                name="unique_payment_borrowing_and_payment_type",
            ),
        ]

    def __str__(self):
        return (
            f"Payment for Borrowing ID {self.borrowing_id}. "
            f"Type: {self.payment_type}. Status: {self.payment_status}."
        )

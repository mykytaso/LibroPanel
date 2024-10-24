from rest_framework import serializers

from borrowings.serializers import BorrowingSerializer
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = (
            "id",
            "payment_status",
            "payment_type",
            "borrowing",
            "amount_to_pay",
        )


class PaymentDetailSerializer(serializers.ModelSerializer):
    borrowing = BorrowingSerializer()

    class Meta:
        model = Payment
        fields = (
            "id",
            "payment_status",
            "payment_type",
            "borrowing",
            "session_url",
            "session_id",
            "amount_to_pay",
        )

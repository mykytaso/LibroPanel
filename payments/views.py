import stripe
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from borrowings.helpers.payment import create_checkout_session
from borrowings.helpers.telegram import send_message
from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentDetailSerializer,
)


class PaymentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Payment.objects.all().select_related()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            Payment.objects.all()
            if self.request.user.is_staff
            else Payment.objects.filter(borrowing__user=self.request.user)
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentSerializer
        return PaymentDetailSerializer


class PaymentRenewView(APIView):
    def patch(self, request, pk: int) -> Response:
        db_checkout_session = Payment.objects.get(pk=pk)

        # If the checkout session is expired: creates a new Stripe checkout session and updates it in the database
        if db_checkout_session.payment_status == Payment.PaymentStatus.EXPIRED:
            renewed_stripe_checkout_session = create_checkout_session(
                borrowing=db_checkout_session.borrowing,
                amount_to_pay=db_checkout_session.amount_to_pay,
                payment_type=db_checkout_session.payment_type,
            )

            return Response(
                {
                    "detail": "Checkout session renewed successfully",
                    "stripe_session_url": renewed_stripe_checkout_session["url"],
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Checkout session is not expired"},
            status=status.HTTP_404_NOT_FOUND,
        )


class PaymentSuccessView(APIView):
    def get(self, request, *args, **kwargs) -> Response:
        session_id = request.query_params.get("session_id")

        stripe_checkout_session = stripe.checkout.Session.retrieve(session_id)

        db_checkout_session = Payment.objects.select_related(
            "borrowing__user", "borrowing__book"
        ).get(session_id=session_id)

        db_checkout_session.payment_status = stripe_checkout_session.get(
            "payment_status"
        )
        db_checkout_session.save()

        send_message(
            f"💸 Payment received\n"
            f"User {db_checkout_session.borrowing.user} has made "
            f"{db_checkout_session.payment_type.replace('_', ' ')} "
            f"${db_checkout_session.amount_to_pay} for the "
            f"book: '{db_checkout_session.borrowing.book.title}'"
        )

        return Response({"detail": "Payment was successful!"})


class PaymentCancelView(APIView):
    def get(self, request, *args, **kwargs) -> Response:
        return Response(
            {
                "detail": "Your payment session is available for 24 hours. "
                "Please complete the payment within this time."
            }
        )

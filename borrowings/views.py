from decimal import Decimal

import stripe
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action as action_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.models import Book
from borrowings.helpers.borrowing_calculations import (
    calculate_borrowing_price,
    calculate_overdue_fee,
)
from borrowings.helpers.payment import create_checkout_session
from borrowings.helpers.telegram import send_message
from borrowings.models import Borrowing
from borrowings.serializers import (
    ReturnBorrowingSerializer,
    BorrowingCreateSerializer,
    BorrowingSerializer,
    BorrowingDetailSerializer,
)
from library_service import settings
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class BorrowingViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Borrowing.objects.all()
    permission_classes = [IsAuthenticated]

    @staticmethod
    def param_to_bool(param: str) -> bool:
        if param.lower() == "true":
            return True
        if param.lower() == "false":
            return False

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        queryset = (
            Borrowing.objects.all().select_related("book", "user")
            if self.request.user.is_staff
            else Borrowing.objects.select_related("book", "user").filter(
                user=self.request.user
            )
        )

        if is_active:
            queryset = queryset.filter(is_active=self.param_to_bool(is_active))

        if user_id and self.request.user.is_staff:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        if self.action == "return_book":
            return ReturnBorrowingSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingSerializer

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        user = self.request.user

        # Checks whether user has unpaid (pending and expired) checkout sessions
        db_unpaid_checkout_sessions = Payment.objects.filter(
            Q(payment_status=Payment.PaymentStatus.PENDING)
            | Q(payment_status=Payment.PaymentStatus.EXPIRED),
            borrowing__user=user,
        )

        if db_unpaid_checkout_sessions:
            # Sends telegram message about unpaid checkout sessions of the user
            db_unpaid_sessions_count = db_unpaid_checkout_sessions.count()
            send_message(
                f"⚠️ Warning\n"
                f"User {user} has {db_unpaid_sessions_count} unpaid checkout "
                f"session{'s' if db_unpaid_sessions_count > 1 else ''}."
            )

            # Returns a response with list of links to all unpaid checkout sessions of the user
            return Response(
                {
                    "detail": "To make a new borrowing, you need to pay for all unpaid checkout sessions.",
                    "stripe_session_urls": [
                        db_session.session_url
                        for db_session in db_unpaid_checkout_sessions
                    ],
                },
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        borrowing = serializer.save(user=user)

        # Decrease the number of books in the library by one
        book = Book.objects.get(pk=serializer.data["book"])
        book.borrow_one_copy()
        book.save()

        # Creates Stripe checkout session and payment object in db
        stripe_checkout_session = create_checkout_session(
            borrowing=borrowing,
            amount_to_pay=calculate_borrowing_price(borrowing),
            payment_type=Payment.PaymentType.BORROWING_PAYMENT,
        )

        send_message(
            f"📙 Borrowing \n"
            f"User {user} has borrowed the book: '{book.title}' on {serializer.data['borrow_date']}. "
            f"The expected return date is {serializer.data['expected_return_date']}."
        )

        return Response(
            {
                "detail": "Borrowing created successfully",
                "stripe_session_url": stripe_checkout_session["url"],
            },
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    @action_decorator(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="return",
    )
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing, data=request.data)
        serializer.is_valid(raise_exception=True)

        # Increase the number of books in the library by one
        borrowing.book.return_one_copy()
        borrowing.book.save()

        borrowing.actual_return_date = timezone.localdate()
        borrowing.is_active = False

        serializer.save()

        # Calculates overdue fee
        overdue_fee = calculate_overdue_fee(borrowing)

        response = Response(serializer.data, status=status.HTTP_200_OK)

        # Creates Stripe checkout session and updates payment object in db (if overdue fee > 0)
        if overdue_fee > Decimal(0):
            stripe_checkout_session = create_checkout_session(
                borrowing=borrowing,
                amount_to_pay=calculate_overdue_fee(borrowing),
                payment_type=Payment.PaymentType.OVERDUE_FEE_PAYMENT,
            )

            response = Response(
                {
                    "detail": "Borrowing returned successfully",
                    "stripe_session_url": stripe_checkout_session["url"],
                },
                status=status.HTTP_201_CREATED,
            )

        send_message(
            f"📗 Returning \n"
            f"User {borrowing.user.email} has returned the "
            f"book: '{borrowing.book.title}' on {borrowing.actual_return_date}."
        )

        return response

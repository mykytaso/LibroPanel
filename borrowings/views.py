from decimal import Decimal

import stripe
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
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

        # Staff can view all borrowings, while customers can only see their own.
        queryset = (
            Borrowing.objects.all().select_related("book", "user")
            if self.request.user.is_staff
            else Borrowing.objects.select_related("book", "user").filter(
                user=self.request.user
            )
        )

        # All logged-in users can filter borrowings by is_active
        if is_active:
            queryset = queryset.filter(is_active=self.param_to_bool(is_active))

        # Staff can additionally filter borrowings by user_id
        if user_id and self.request.user.is_staff:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "is_active",
                type=bool,
                description="Filter by is_active. Choose true or false.",
            ),
            OpenApiParameter(
                "user_id",
                type=int,
                description="Filter by user_id "
                "(This functionality available only for Staff)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
        db_unpaid_checkout_session = Payment.objects.filter(
            Q(payment_status=Payment.PaymentStatus.PENDING)
            | Q(payment_status=Payment.PaymentStatus.EXPIRED),
            borrowing__user=user,
        ).first()

        if db_unpaid_checkout_session:
            # Sends telegram message about unpaid checkout session of the user
            send_message(
                f"⚠️ <b>Warning</b>\n"
                f"User <b>{user}</b> has unpaid checkout session:\n"
                f"{db_unpaid_checkout_session}\n"
                f"<a href='{db_unpaid_checkout_session.session_url}'><b>Pay Now</b></a>"
            )

            # Returns a response with link to unpaid checkout session
            return Response(
                {
                    "detail": "To make a new borrowing, you need to pay for unpaid checkout session.",
                    "stripe_session_url": db_unpaid_checkout_session.session_url,
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
            request=self.request,
            borrowing=borrowing,
            amount_to_pay=calculate_borrowing_price(borrowing),
            payment_type=Payment.PaymentType.BORROWING_PAYMENT,
        )

        send_message(
            f"📙 <b>Borrowing</b> \n"
            f"User <b>{user}</b> has borrowed the book: <b>{book.title}</b> on {serializer.data['borrow_date']}.\n"
            f"Expected return date: {serializer.data['expected_return_date']}.\n"
            f"<a href='{stripe_checkout_session['url']}'><b>Pay</b></a>"
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
                request=self.request,
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
            f"📗 <b>Returning</b> \n"
            f"User <b>{borrowing.user.email}</b> has returned the "
            f"book: <b>{borrowing.book.title}</b> on {borrowing.actual_return_date}."
        )

        return response

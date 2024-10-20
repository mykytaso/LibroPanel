from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action as action_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.models import Book
from borrowings.helpers.telegram import send_message
from borrowings.models import Borrowing
from borrowings.serializers import (
    ReturnBorrowingSerializer,
    BorrowingCreateSerializer,
    BorrowingSerializer,
)


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
        return BorrowingSerializer

    def perform_create(self, serializer):
        if self.request.user:
            serializer.save(user=self.request.user)

            book = Book.objects.get(pk=serializer.data["book"])
            book.borrow_one_copy()
            book.save()

            send_message(
                f"📙 Borrowing \n"
                f"The book '{book.title}' by {book.author} was borrowed by the user "
                f"{self.request.user} on {serializer.data['borrow_date']}. "
                f"The expected return date is {serializer.data['expected_return_date']}."
            )

    @transaction.atomic
    @action_decorator(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="return",
    )
    def return_book(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        instance.book.return_one_copy()
        instance.book.save()

        instance.actual_return_date = timezone.localdate()
        instance.is_active = False

        serializer.save()

        send_message(
            f"📗 Returning \n"
            f"The book '{instance.book.title}' by {instance.book.author} was returned by the user "
            f"{instance.user.email} on {instance.actual_return_date}. "
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

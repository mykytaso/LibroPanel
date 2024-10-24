from django.utils import timezone

from .borrowing_calculations import calculate_overdue_days, calculate_overdue_fee
from .telegram import send_message
from ..models import Borrowing


def send_overdue_alert_message():
    borrowings = Borrowing.objects.select_related("user", "book")
    message = ""
    count = 0

    for borrowing in borrowings:
        if borrowing.is_active:
            if borrowing.expected_return_date == timezone.localdate():
                message = (
                    f"⚠️ Return Reminder\n"
                    f"User {borrowing.user} should return the book "
                    f"'{borrowing.book.title}' today."
                )
            elif (
                borrowing.expected_return_date
                == timezone.localdate() + timezone.timedelta(days=1)
            ):
                message = (
                    f"⚠️ Return Reminder️\n"
                    f"User {borrowing.user} should return the book "
                    f"'{borrowing.book.title}' tomorrow."
                )
            elif borrowing.expected_return_date < timezone.localdate():
                message = (
                    f"⚠️ Overdue Alert\n"
                    f"User {borrowing.user} should return the overdue book '{borrowing.book.title}' as soon as possible!\n\n"
                    f"Due date: {borrowing.expected_return_date}\n"
                    f"Overdue: {calculate_overdue_days(borrowing)} days\n"
                    f"Fee: ${calculate_overdue_fee(borrowing)}\n"
                )

            send_message(message)
            count += 1

    if count == 0:
        send_message("🎉 No borrowings overdue today!")

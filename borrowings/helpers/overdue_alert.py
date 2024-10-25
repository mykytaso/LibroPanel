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
                    f"⚠️ <b>Return Reminder</b>\n"
                    f"User <b>{borrowing.user}</b> should return the book "
                    f"<b>{borrowing.book.title}</b> <b>today</b>."
                )
            elif (
                borrowing.expected_return_date
                == timezone.localdate() + timezone.timedelta(days=1)
            ):
                message = (
                    f"⚠️ <b>Return Reminder️</b>\n"
                    f"User <b>{borrowing.user}</b> should return the book "
                    f"<b>{borrowing.book.title}</b> <b>tomorrow</b>."
                )
            elif borrowing.expected_return_date < timezone.localdate():
                message = (
                    f"⚠️ <b>Overdue Alert</b>\n"
                    f"User <b>{borrowing.user}</b> should return the overdue book <b>{borrowing.book.title}</b> as soon as possible!\n\n"
                    f"Due date: {borrowing.expected_return_date}\n"
                    f"Overdue: {calculate_overdue_days(borrowing)} days\n"
                    f"Fee: ${calculate_overdue_fee(borrowing)}\n"
                )

            send_message(message)
            count += 1

    if count == 0:
        send_message("🎉 <b>No borrowings overdue today!</b>")

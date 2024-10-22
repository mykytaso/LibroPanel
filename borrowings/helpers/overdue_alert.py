from django.utils import timezone

from .borrowing_calculations import calculate_overdue_days, calculate_overdue_fee
from .telegram import send_message
from ..models import Borrowing


def send_overdue_alert_message():
    instances = Borrowing.objects.select_related("user", "book")
    message = ""
    count = 0

    for instance in instances:
        if instance.is_active:
            if instance.expected_return_date == timezone.localdate():
                message = (
                    f"📕 Return Reminder ⚠️\n\n"
                    f"The book '{instance.book.title}' by {instance.book.author} "
                    f"borrowed by user: {instance.user} should be returned today."
                )
            elif (
                instance.expected_return_date
                == timezone.localdate() + timezone.timedelta(days=1)
            ):
                message = (
                    f"📕 Return Reminder ⚠️\n\n"
                    f"The book '{instance.book.title}' by {instance.book.author} "
                    f"borrowed by user: {instance.user} should be returned tomorrow."
                )
            elif instance.expected_return_date < timezone.localdate():
                message = (
                    f"📕 Overdue Alert ⚠️\n\n"
                    f"The book '{instance.book.title}' by {instance.book.author}, "
                    f"borrowed by {instance.user}, is overdue!\n\n"
                    f"Due date: {instance.expected_return_date}\n"
                    f"{calculate_overdue_days(instance)} days overdue\n"
                    f"Fee: ${calculate_overdue_fee(instance)}\n"
                )

            send_message(message)
            count += 1

    if count == 0:
        send_message("🎉 No borrowings overdue today!")

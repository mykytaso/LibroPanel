from celery import shared_task

from borrowings.helpers.overdue import send_overdue_alert_message


@shared_task
def overdue_check() -> None:
    send_overdue_alert_message()

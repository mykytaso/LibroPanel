from celery import shared_task

from borrowings.helpers.expired_sessions import expired_sessions_check
from borrowings.helpers.overdue_alert import send_overdue_alert_message


@shared_task
def send_overdue_alert_message_task() -> None:
    send_overdue_alert_message()


@shared_task
def expired_sessions_check_task() -> None:
    expired_sessions_check()

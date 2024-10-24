from decimal import Decimal

from django.utils import timezone


def calculate_borrowing_price(borrowing) -> Decimal:
    return (
        borrowing.book.daily_fee
        * (borrowing.expected_return_date - borrowing.borrow_date).days
    )


def calculate_overdue_fee(borrowing) -> Decimal:
    return borrowing.book.daily_fee * calculate_overdue_days(borrowing)


def calculate_overdue_days(borrowing) -> int:
    expected_return_date = borrowing.expected_return_date
    today = timezone.localdate()

    if expected_return_date < today:
        return (today - expected_return_date).days

    return 0

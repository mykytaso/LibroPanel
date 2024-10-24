def validate_book_not_already_returned(actual_return_date, error_to_raise) -> None:
    """
    Validates that the book has not been already returned.
    """
    if actual_return_date:
        raise error_to_raise({"is_active": "This book has already been returned."})


def validate_book_availability(copies: int, error_to_raise) -> None:
    """
    Validates that there are available copies of the book.
    """
    if copies <= 0:
        raise error_to_raise(
            {"book": "Sorry, there are no available copies of this book left."}
        )


def validate_non_past_return_date(
    borrow_date, expected_return_date, error_to_raise
) -> None:
    """
    Validates that the expected return date is not earlier than the borrow date.
    """
    if expected_return_date <= borrow_date:
        raise error_to_raise(
            {"expected_return_date": "Expected return date cannot be in the past."}
        )

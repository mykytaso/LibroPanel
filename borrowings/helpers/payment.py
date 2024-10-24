import stripe
from django.conf import settings

from payments.models import Payment


def create_checkout_session(borrowing, amount_to_pay, payment_type):

    # Creates Stripe checkout session
    stripe_checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{payment_type.capitalize().replace('_', ' ')} "
                        "for "
                        f"{borrowing.book.title}",
                    },
                    "unit_amount": int(amount_to_pay * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=(settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}"),
        cancel_url=(settings.STRIPE_CANCEL_URL + "?session_id={CHECKOUT_SESSION_ID}"),
    )

    # Updates or creates checkout session (payment object) in db
    Payment.objects.update_or_create(
        borrowing=borrowing,
        payment_status=Payment.PaymentStatus.EXPIRED,
        defaults={
            "payment_status": Payment.PaymentStatus.PENDING,
            "payment_type": payment_type,
            "session_url": stripe_checkout_session.url,
            "session_id": stripe_checkout_session.id,
            "amount_to_pay": amount_to_pay,
        },
    )

    return stripe_checkout_session

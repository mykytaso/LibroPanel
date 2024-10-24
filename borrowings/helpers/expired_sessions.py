import stripe

from library_service import settings
from payments.models import Payment


def expired_sessions_check() -> None:
    stripe.api_key = settings.STRIPE_SECRET_KEY

    db_checkout_sessions = Payment.objects.filter(
        payment_status=Payment.PaymentStatus.PENDING
    )

    for db_checkout_session in db_checkout_sessions:
        stripe_checkout_session = stripe.checkout.Session.retrieve(
            db_checkout_session.session_id
        )

        if stripe_checkout_session["status"] == Payment.PaymentStatus.EXPIRED:
            db_checkout_session.payment_status = Payment.PaymentStatus.EXPIRED
            db_checkout_session.save()

from django.urls import path, include
from rest_framework import routers

from payments.views import (
    PaymentViewSet,
    PaymentRenewView,
    PaymentCancelView,
    PaymentSuccessView,
)

app_name = "payments"

router = routers.DefaultRouter()
router.register("", PaymentViewSet)


urlpatterns = [
    path("success/", PaymentSuccessView.as_view(), name="checkout-success"),
    path("<int:pk>/renew/", PaymentRenewView.as_view(), name="checkout-renew"),
    path("cancel/", PaymentCancelView.as_view(), name="checkout-cancel"),
    path("", include(router.urls)),
]

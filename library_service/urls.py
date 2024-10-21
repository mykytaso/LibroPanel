from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/books/", include("books.urls", namespace="book")),
    path("api/users/", include("users.urls", namespace="user")),
    path("api/borrowings/", include("borrowings.urls", namespace="borrowing")),
    path("api/payments/", include("payments.urls", namespace="payment")),
] + debug_toolbar_urls()

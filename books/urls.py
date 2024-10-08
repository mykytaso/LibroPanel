from django.urls import path, include
from books.views import BookViewSet
from rest_framework import routers

app_name = "books"

router = routers.DefaultRouter()

router.register("books", BookViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

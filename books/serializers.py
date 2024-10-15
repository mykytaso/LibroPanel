from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "copies", "daily_fee")


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "copies")

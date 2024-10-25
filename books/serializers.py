from decimal import Decimal

from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "copies", "daily_fee")

    def validate(self, attrs):
        if attrs["daily_fee"] < Decimal("0.50"):
            raise serializers.ValidationError(
                {"daily_fee": "Daily fee must be at least $0.50"}
            )
        return attrs


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "copies")

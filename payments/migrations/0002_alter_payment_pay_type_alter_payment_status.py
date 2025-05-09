# Generated by Django 5.1.1 on 2024-10-21 23:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="pay_type",
            field=models.CharField(
                choices=[("Payment", "Payment"), ("Fine", "Fine")],
                default="P",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Paid", "Paid"),
                    ("Expired", "Expired"),
                ],
                default="P",
                max_length=20,
            ),
        ),
    ]

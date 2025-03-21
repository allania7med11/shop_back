# Generated by Django 4.0.5 on 2023-10-20 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0005_order_alter_product_options_orderitems"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="total_amount",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name="orderitems",
            name="subtotal",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]

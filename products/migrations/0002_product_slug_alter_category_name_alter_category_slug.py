# Generated by Django 4.0.5 on 2023-01-08 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="slug",
            field=models.SlugField(
                editable=False,
                max_length=100,
                null=True,
                unique=True,
                verbose_name="Slug",
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=250, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(
                editable=False,
                max_length=100,
                unique=True,
                verbose_name="Slug",
            ),
        ),
    ]

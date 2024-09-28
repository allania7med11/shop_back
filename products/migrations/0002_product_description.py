# Generated by Django 4.0.5 on 2023-01-03 20:30

import django_quill.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="description",
            field=django_quill.fields.QuillField(
                blank=True, null=True, verbose_name="Description"
            ),
        ),
    ]

# Generated by Django 4.0.5 on 2025-02-21 06:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="message",
            options={"ordering": ["created_at"]},
        ),
    ]

from django.db import models


class CommandHistory(models.Model):
    name = models.CharField("Name of command", max_length=200)
    applied_at = models.DateTimeField(auto_now_add=True)

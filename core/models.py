from django.db import models
import uuid

class CommandHistory(models.Model):
    name = models.CharField("Name of command", max_length=200)
    applied_at = models.DateTimeField(auto_now_add=True)
    

class Guest(models.Model):
    guest_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Guest #{self.id}"
from django.apps import AppConfig


class AIConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai"

    def ready(self):
        from .signals import register_product_signals

        register_product_signals()

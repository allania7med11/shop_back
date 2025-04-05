import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from products.models import Category, Product
from products.tasks import rebuild_product_index_task

logger = logging.getLogger(__name__)


def get_product_signature(product: Product) -> str:
    """Create a signature of product data that affects AI responses"""
    try:
        return (
            f"{product.name}::{product.price.amount}::{product.price.currency}::"
            f"{product.description.html}::{product.category.slug}::"
            f"{product.category.name}::{product.slug}"
        )
    except AttributeError as e:
        # Log the error if needed
        logger.error(f"Attribute error while creating product signature: {str(e)}")
        return ""
    except Exception as e:
        # Optionally catch other exceptions
        logger.error(f"An unexpected error occurred: {str(e)}")
        return ""


@receiver(pre_save, sender=Product)
def handle_product_pre_save(sender, instance, **kwargs):
    """Handle product pre-save to detect changes"""
    if not kwargs.get("raw", False) and instance.pk:  # Only for existing products
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if get_product_signature(old_instance) != get_product_signature(instance):
                # Mark that content has changed for post_save handler
                instance._content_changed = True
        except Product.DoesNotExist:
            pass


@receiver([post_save, post_delete], sender=Product)
def handle_product_change(sender, instance, **kwargs):
    """Handle product changes by scheduling a rebuild"""
    if kwargs.get("created", False):
        schedule_rebuild(f"Product {instance.name} created")
    elif kwargs.get("raw", False):
        schedule_rebuild(f"Product {instance.name} updated via raw save")
    elif hasattr(instance, "_content_changed") and instance._content_changed:
        schedule_rebuild(f"Product {instance.name} content changed")
    elif kwargs.get("signal") == post_delete:
        schedule_rebuild(f"Product {instance.name} deleted")


@receiver(post_save, sender=Category)
def handle_category_change(sender, instance, **kwargs):
    """Handle category changes that affect products"""
    if instance.products.exists():
        schedule_rebuild(f"Category {instance.name} changed affecting products")


def schedule_rebuild(reason: str):
    """Schedule a delayed rebuild with logging"""
    rebuild_product_index_task.delay(reason)


def register_product_signals():
    """Register all product-related signals"""
    from django.apps import apps

    Product = apps.get_model("products", "Product")
    Category = apps.get_model("products", "Category")

    pre_save.connect(handle_product_pre_save, sender=Product)
    post_save.connect(handle_product_change, sender=Product)
    post_save.connect(handle_category_change, sender=Category)
    post_delete.connect(handle_product_change, sender=Product)

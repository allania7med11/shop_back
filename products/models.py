from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from cloudinary.models import CloudinaryField
from djmoney.models.fields import MoneyField
from django_quill.fields import QuillField
from core.models import Guest
from products.managers import ProductManager

from products.utils.slugify import unique_slugify


class Product(models.Model):
    objects = ProductManager()
    name = models.CharField("Product Name", max_length=250)
    slug = models.SlugField("Slug", max_length=100, unique=True, null=True, editable=False)
    price = MoneyField(max_digits=19, decimal_places=4, default_currency="USD")
    discount = models.ForeignKey(
        "Discount",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    category = models.ForeignKey(
        "Category",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    description = QuillField("Description", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, **kwargs):
        unique_slugify(self, self.name) 
        super(Product, self).save(**kwargs)
    
    class Meta:
        ordering = ['-updated_at']


class Discount(models.Model):
    name = models.CharField("Name", max_length=250)
    percent = models.DecimalField("Percentage", max_digits=5, decimal_places=2)
    active = models.BooleanField("Active", default=True)

    def __str__(self):
        return self.name


class File(models.Model):
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="files"
    )
    name = models.CharField("Name", max_length=250, blank=True, null=True)
    file = CloudinaryField("file")

    def get_url(self):
        return self.file.build_url()


class Category(models.Model):
    name = models.CharField("Name", max_length=250)
    slug = models.SlugField("Slug", max_length=100, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, **kwargs):
        unique_slugify(self, self.name) 
        super(Category, self).save(**kwargs)

class Order(models.Model):
    DRAFT = 'draft'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELED = 'canceled'

    class OrderStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELED = 'canceled', 'Canceled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=50, choices=OrderStatus.choices, default=OrderStatus.DRAFT)

    def __str__(self):
        return f"Order #{self.id} ({self.get_status_display()})"

class OrderItems(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)  
    product = models.ForeignKey('Product', on_delete=models.PROTECT)  
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)]
)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product}"

    class Meta:
        verbose_name_plural = "Order Items"
        unique_together = ('order', 'product')
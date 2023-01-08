from django.db import models
from cloudinary.models import CloudinaryField
from djmoney.models.fields import MoneyField
from django_quill.fields import QuillField

from products.utils.slugify import unique_slugify


class Product(models.Model):
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

    def __str__(self):
        return self.name
    def save(self, **kwargs):
        unique_slugify(self, self.name) 
        super(Product, self).save(**kwargs)


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

    def __str__(self):
        return self.name
    
    def save(self, **kwargs):
        unique_slugify(self, self.name) 
        super(Category, self).save(**kwargs)

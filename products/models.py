from django.db import models
from cloudinary.models import CloudinaryField
from djmoney.models.fields import MoneyField

class Product(models.Model):
    name = models.CharField("Product Name", max_length=250)
    price = MoneyField(max_digits=19, decimal_places=4, default_currency='USD')
    discount = models.ForeignKey("Discount", blank=True, null=True, on_delete=models.SET_NULL, related_name="products")
    category = models.ForeignKey("Category", blank=True, null=True, on_delete=models.SET_NULL, related_name="products")


class Discount(models.Model):
    name = models.CharField("Name", max_length=250)
    percent = models.DecimalField("Percentage", max_digits=5, decimal_places=2)
    active = models.BooleanField("Active", default=True)


class File(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="files")
    name = models.CharField("Name", max_length=250, blank=True, null=True)
    file = CloudinaryField('file')

class Category(models.Model):
    name = models.CharField("Name", max_length=250, blank=True, null=True)
    slug = models.SlugField("Slug", max_length=100, unique=True)
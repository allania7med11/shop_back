from django.db import models
from cloudinary.models import CloudinaryField
# Create your models here.
class Product(models.Model):
    name = models.CharField("Product Name", max_length=250)
    discount = models.ForeignKey("Discount", blank=True, null=True)


class Discount(models.Model):
    name = models.CharField("Name", max_length=250)
    discount_percent = models.DecimalField("Percentage", max_digits=4, decimal_places=2)
    active = models.BooleanField("Active", default=True)


class File(models.Model):
    name = models.CharField("Name", max_length=250, blank=True, null=True)
    image = CloudinaryField('file')
    active = models.BooleanField("Active", default=True)

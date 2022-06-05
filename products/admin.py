from django.contrib import admin
from products.models import Product, Discount, File, Category

# Register your models here.
admin.site.register(Product)
admin.site.register(Discount)
admin.site.register(File)
admin.site.register(Category)
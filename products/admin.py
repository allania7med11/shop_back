from django.contrib import admin
from products.models import Product, Discount, File, Category

# Register your models here.
admin.site.register(Discount)
admin.site.register(File)
admin.site.register(Category)


class FileInline(admin.TabularInline):
    model = File


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [
        FileInline,
    ]

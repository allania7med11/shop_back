from django.contrib import admin
from products.models import Product, Discount, File, Category

admin.site.site_header = "Shoppingify Admin"
admin.site.site_title = "Shoppingify Admin Portal"
admin.site.index_title = "Welcome to Shoppingify Portal"

# Register your models here.
admin.site.register(Discount)
admin.site.register(File)


class FileInline(admin.TabularInline):
    model = File


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [
        FileInline,
    ]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ['name']

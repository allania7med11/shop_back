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
    list_display = ["name", "price","discount", "category","updated_at"]
    list_filter = ('category',)
    inlines = [
        FileInline,
    ]
    search_fields = ['name', 'description']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ['name']

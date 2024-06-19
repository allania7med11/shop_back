from django.contrib import admin
from products.models import Order, OrderAddress, OrderItems, Product, Discount, File, Category

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


class OrderAddressInline(admin.StackedInline):
    model = OrderAddress
    can_delete = False
    verbose_name_plural = 'Order Address'

class OrderItemsInline(admin.TabularInline):
    model = OrderItems
    extra = 1
    verbose_name_plural = 'Order Items'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'total_amount', 'status')

    inlines = [OrderAddressInline, OrderItemsInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(status=Order.OrderStatus.DRAFT)

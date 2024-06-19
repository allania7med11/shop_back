from django.contrib import admin
from django import forms
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
    list_filter = ("category",)
    inlines = [
        FileInline,
    ]
    search_fields = ["name", "description"]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ["name"]


class OrderAddressInline(admin.StackedInline):
    model = OrderAddress
    can_delete = False
    verbose_name_plural = "Order Address"

class OrderItemsInlineForm(forms.ModelForm):
    class Meta:
        model = OrderItems
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subtotal"].widget.attrs["readonly"] = True
        self.fields["subtotal"].widget.attrs["style"] = "pointer-events: none; background-color: #f0f0f0;"

class OrderItemsInline(admin.TabularInline):
    model = OrderItems
    form = OrderItemsInlineForm  
    extra = 1
    verbose_name_plural = "Order Items"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order_date", "total_amount", "status")
    readonly_fields = ("total_amount",)

    inlines = [OrderAddressInline, OrderItemsInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(status=Order.OrderStatus.DRAFT)
    

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.set_total_amount()


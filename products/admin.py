from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from products.models import Category, Discount, File, Order, OrderAddress, OrderItems, Product

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
    list_display = ["name", "price", "discount", "category", "updated_at"]
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
        self.fields["subtotal"].widget.attrs[
            "style"
        ] = "pointer-events: none; background-color: #f0f0f0;"


class OrderItemsInline(admin.TabularInline):
    model = OrderItems
    form = OrderItemsInlineForm
    extra = 1
    verbose_name_plural = "Order Items"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_display",
        "order_date",
        "total_amount",
        "status",
    )
    readonly_fields = ("total_amount", "user_link", "user_email")
    exclude = ("user",)

    inlines = [OrderAddressInline, OrderItemsInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(status=Order.OrderStatus.DRAFT)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.set_total_amount()

    def user_display(self, obj: Order):
        user = obj.user
        full_name = f"{user.first_name} {user.last_name}".strip()
        if full_name:
            return full_name
        return obj.user.email.split("@")[0]

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"

    def user_link(self, obj):
        link = reverse("admin:auth_user_change", args=[obj.user.id])
        full_name = self.user_display(obj)
        return format_html('<a href="{}">{}</a>', link, full_name)

    user_link.short_description = "User"

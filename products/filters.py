from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Product

class DiscountFilter(filters.RangeFilter):
    def filter(self, qs, value):
        if value:
            qs = qs.filter(discount__active=True)
        return super().filter(qs, value)

class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass

class ProductFilter(filters.FilterSet):
    category = filters.CharFilter(field_name='category__slug')
    search = filters.CharFilter(method='filter_search', label='Search In Name/Description')
    current_price = filters.RangeFilter(label='Current Price')
    discount = DiscountFilter(field_name='discount__percent')
    id_in = NumberInFilter(field_name='id', lookup_expr='in')
    ordering = filters.OrderingFilter(
        fields=(
            ('current_price', 'current_price'),
            ('name', 'name'),
        ),
    )

    class Meta:
        model = Product
        fields = ['category', 'search', 'current_price', 'discount', 'id_in']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))
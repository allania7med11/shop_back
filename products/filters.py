from django_filters import rest_framework as filters
from django.db.models import Q
from djmoney.money import Money
from .models import Product

class ProductFilter(filters.FilterSet):
    category = filters.CharFilter(field_name='category__slug')
    search = filters.CharFilter(method='filter_search')
    price_min = filters.NumberFilter(method='filter_price_min', lookup_expr='range')
    price_max = filters.NumberFilter(method='filter_price_max')

    class Meta:
        model = Product
        fields = ['category', 'search', 'price_min', "price_max"]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))
    
    def filter_price_min(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(price__gte=Money(value, 'USD'))
    
    def filter_price_max(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(price__lte=Money(value, 'USD'))
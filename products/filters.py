from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Product

class ProductFilter(filters.FilterSet):
    category = filters.CharFilter(field_name='category__slug')
    search = filters.CharFilter(method='filter_search')
    current_price = filters.RangeFilter()

    class Meta:
        model = Product
        fields = ['category', 'search', 'current_price']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))
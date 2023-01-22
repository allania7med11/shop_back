from unittest import case
from django.db.models import F, Case, When, DecimalField
from rest_framework import viewsets
from products.filters import ProductFilter
from products.models import Category, Product

from products.serializers import CategorySerializer, ProductSerializer
from rest_framework import permissions


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_class = ProductFilter
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            current_price=Case(
                When(
                    discount__isnull=False,
                    discount__active=True,
                    then=F("price") * (1 - F("discount__percent") / 100),
                ),
                default=F("price"),
                output_field=DecimalField(),
            )
        )
        return queryset


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]
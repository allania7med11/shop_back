from django.db.models import F, Case, When, DecimalField
from rest_framework import viewsets
from products.filters import ProductFilter
from products.models import Category, OrderItems, Product

from products.serializers import (
    CartItemsSerializer,
    CategorySerializer,
    ProductSerializer,
)
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from products.utils.orders import get_current_draft_order, get_existing_or_new_order_item


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
        return queryset


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]


class CartItemsViewSet(viewsets.ModelViewSet):
    queryset = OrderItems.objects.all()
    serializer_class = CartItemsSerializer

    def initiate_cart(self, request):
        self.cart = get_current_draft_order(request)

    def get_queryset(self):
        return OrderItems.objects.filter(order=self.cart)

    def create(self, request, *args, **kwargs):
        self.initiate_cart(request)
        instance = get_existing_or_new_order_item(self.cart, request.data["product"])
        serializer = self.get_serializer(data=request.data, instance=instance)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        self.initiate_cart(request)
        return super().list(request, *args, **kwargs)

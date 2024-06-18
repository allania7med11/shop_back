from rest_framework import viewsets
from products.filters import ProductFilter
from products.mixins import CartInitiationMixin
from products.models import Category, OrderAddress, OrderItems, Product

from products.serializers import (
    CartAddressSerializer,
    CartItemsSerializer,
    CategorySerializer,
    ProductSerializer,
)
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from products.utils.orders import  get_existing_or_new_order_address, get_existing_or_new_order_item, set_order_to_processing


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_class = ProductFilter
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]



class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]
    



class CartItemsViewSet(CartInitiationMixin, viewsets.ModelViewSet):
    queryset = OrderItems.objects.all()
    serializer_class = CartItemsSerializer

    def get_queryset(self):
        return OrderItems.objects.filter(order=self.cart)

    def create(self, request, *args, **kwargs):
        instance = get_existing_or_new_order_item(self.cart, request.data["product"])
        serializer = self.get_serializer(data=request.data, instance=instance)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CardAddressViewSet(CartInitiationMixin, viewsets.ModelViewSet):
    queryset = OrderAddress.objects.all()
    serializer_class = CartAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderAddress.objects.filter(order=self.cart)

    def create(self, request, *args, **kwargs):
        order = self.cart 
        if not order.user == self.request.user:
            return Response({"detail": "Order not found for the current user."}, status=status.HTTP_400_BAD_REQUEST)
        
        if order.is_empty():
            return Response({"detail": "Order cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        instance = get_existing_or_new_order_address(order, request.data)
        serializer = self.get_serializer(data=request.data, instance=instance)
        if serializer.is_valid():
            serializer.save()
            set_order_to_processing(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

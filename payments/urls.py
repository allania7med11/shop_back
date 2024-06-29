from django.urls import path
from .views import PaymentAPI, test_payment

urlpatterns = [
    path("make/", PaymentAPI.as_view(), name='make_payment'),
    path("test-payment/", test_payment),
]
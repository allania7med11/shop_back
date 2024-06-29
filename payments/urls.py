from django.urls import path
from .views import PaymentAPI, save_stripe_info, test_payment

urlpatterns = [
    path("make/", PaymentAPI.as_view(), name='make_payment'),
    path("test-payment/", test_payment),
    path("save-stripe-info/", save_stripe_info),
]
import json
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import CardInformationSerializer
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(["POST"])
def test_payment(request):
    test_payment_intent = stripe.PaymentIntent.create(
        amount=1000, currency="pln", 
        payment_method_types=["card"],
        receipt_email="test@example.com")
    return Response(status=status.HTTP_200_OK, data=test_payment_intent)



def save_stripe_info(request):
    # Ensure that method is POST and handle JSON loading
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data["email"]
            payment_method_id = data["payment_method_id"]
        except (json.JSONDecodeError, KeyError) as e:
            return JsonResponse({'message': f'Error parsing data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create a customer in Stripe
            customer = stripe.Customer.create(
                email=email,
                payment_method=payment_method_id,
                invoice_settings={
                    'default_payment_method': payment_method_id
                }
            )
            return JsonResponse({'message': 'Success', 'customer_id': customer.id}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            return JsonResponse({'message': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    else:
        return JsonResponse({'message': 'Method Not Allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class PaymentAPI(APIView):
    serializer_class = CardInformationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        response = {}
        if serializer.is_valid():
            data_dict = serializer.validated_data
            response = self.stripe_card_payment(data_dict=data_dict)
        else:
            response = {
                "errors": serializer.errors,
                "status": status.HTTP_400_BAD_REQUEST
            }
                
        return Response(response)

    def stripe_card_payment(self, data_dict):
        try:
            card_details = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": data_dict["card_number"],
                    "exp_month": data_dict["expiry_month"],
                    "exp_year": data_dict["expiry_year"],
                    "cvc": data_dict["cvc"],
                },
            )
            # You can also get the amount from the database by creating a model
            payment_intent = stripe.PaymentIntent.create(
                amount=10000,  # Amount in the smallest currency unit (e.g., 10000 for $100.00)
                currency="inr",
            )
            payment_intent_modified = stripe.PaymentIntent.modify(
                payment_intent["id"],
                payment_method=card_details["id"],
            )
            try:
                payment_confirm = stripe.PaymentIntent.confirm(
                    payment_intent["id"]
                )
                payment_intent_modified = stripe.PaymentIntent.retrieve(payment_intent["id"])
            except Exception as e:
                payment_intent_modified = stripe.PaymentIntent.retrieve(payment_intent["id"])
                payment_confirm = {
                    "stripe_payment_error": "Failed",
                    "code": payment_intent_modified["last_payment_error"]["code"],
                    "message": payment_intent_modified["last_payment_error"]["message"],
                    "status": "Failed"
                }
            if payment_intent_modified and payment_intent_modified["status"] == "succeeded":
                response = {
                    "message": "Card Payment Success",
                    "status": status.HTTP_200_OK,
                    "card_details": card_details,
                    "payment_intent": payment_intent_modified,
                    "payment_confirm": payment_confirm
                }
            else:
                response = {
                    "message": "Card Payment Failed",
                    "status": status.HTTP_400_BAD_REQUEST,
                    "card_details": card_details,
                    "payment_intent": payment_intent_modified,
                    "payment_confirm": payment_confirm
                }
        except Exception as e:
            response = {
                "error": "Your card number is incorrect",
                "status": status.HTTP_400_BAD_REQUEST,
                "payment_intent": {"id": "Null"},
                "payment_confirm": {"status": "Failed"}
            }
        return response

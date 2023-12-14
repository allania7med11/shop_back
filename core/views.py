import uuid
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Guest
from .serializers import GuestSerializer

class GuestCreateView(APIView):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response({'error': 'Cannot create guest while logged in.'}, status=status.HTTP_400_BAD_REQUEST)
        # Generate a new guest_id
        guest_id = str(uuid.uuid4())

        # Create a new Guest instance with the generated guest_id
        guest = Guest.objects.create(guest_id=guest_id)

        serializer = GuestSerializer(guest)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

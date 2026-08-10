from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import (
    IsActiveCodagoraUser,
)

from .serializers import (
    HomeResponseSerializer,
)
from .services import (
    build_home_payload,
)


class HomeView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        payload = (
            build_home_payload(
                user=request.user,
            )
        )

        serializer = (
            HomeResponseSerializer(
                data=payload
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)

from firebase_admin import (
    exceptions as firebase_exceptions,
)

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
)
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth_serializers import (
    LegalAcceptanceSerializer,
    OnboardingCompleteSerializer,
)
from .auth_services import (
    accept_current_legal_documents,
    build_onboarding_requirements,
    complete_onboarding,
    sync_firebase_user,
)
from .auth_utils import (
    get_decoded_token,
    raise_drf_validation_error,
)
from .models import AccountStatus


class FirebaseUnavailable(
    APIException,
):
    status_code = (
        status.HTTP_503_SERVICE_UNAVAILABLE
    )

    default_detail = (
        "認証サービスへ"
        "接続できません。"
    )


class AuthBootstrapView(APIView):
    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request,
    ):
        decoded_token = (
            get_decoded_token(
                request
            )
        )

        try:
            sync_firebase_user(
                user=request.user,
                decoded_token=decoded_token,
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        except firebase_exceptions.FirebaseError:
            raise FirebaseUnavailable

        requirements = (
            build_onboarding_requirements(
                user=request.user,
                decoded_token=decoded_token,
            )
        )

        onboarding_required = (
            request.user.account_status
            in (
                AccountStatus.PROVISIONAL,
                AccountStatus
                .VERIFICATION_REQUIRED,
            )
        )

        deletion_pending = (
            request.user.account_status
            == AccountStatus
            .DELETION_PENDING
        )

        return Response(
            {
                "user": {
                    "id": request.user.id,
                    "email": (
                        request.user.email
                    ),
                    "email_verified": (
                        request.user
                        .email_verified
                    ),
                    "display_name": (
                        request.user
                        .display_name
                    ),
                    "handle": (
                        request.user.handle
                    ),
                },
                "account_status": (
                    request.user
                    .account_status
                ),
                "onboarding_required": (
                    onboarding_required
                ),
                "deletion_pending": (
                    deletion_pending
                ),
                "deletion_scheduled_for": (
                    request.user
                    .deletion_scheduled_for
                ),
                "requirements": (
                    requirements
                ),
            },
            status=status.HTTP_200_OK,
        )


class OnboardingCompleteView(
    APIView,
):
    permission_classes = (
        IsAuthenticated,
    )

    throttle_scope = (
        "auth_sensitive"
    )

    def post(
        self,
        request,
    ):
        serializer = (
            OnboardingCompleteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            user = complete_onboarding(
                user=request.user,
                decoded_token=(
                    get_decoded_token(
                        request
                    )
                ),
                display_name=(
                    serializer
                    .validated_data[
                        "display_name"
                    ]
                ),
                handle=(
                    serializer
                    .validated_data[
                        "handle"
                    ]
                ),
                accept_terms=(
                    serializer
                    .validated_data[
                        "accept_terms"
                    ]
                ),
                accept_privacy=(
                    serializer
                    .validated_data[
                        "accept_privacy"
                    ]
                ),
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        except firebase_exceptions.FirebaseError:
            raise FirebaseUnavailable

        return Response(
            {
                "id": user.id,
                "display_name": (
                    user.display_name
                ),
                "handle": user.handle,
                "account_status": (
                    user.account_status
                ),
                "onboarding_required": (
                    False
                ),
            },
            status=status.HTTP_200_OK,
        )


class LegalAcceptanceView(
    APIView,
):
    permission_classes = (
        IsAuthenticated,
    )

    throttle_scope = (
        "auth_sensitive"
    )

    def post(
        self,
        request,
    ):
        serializer = (
            LegalAcceptanceSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            accept_current_legal_documents(
                user=request.user,
                accept_terms=(
                    serializer
                    .validated_data[
                        "accept_terms"
                    ]
                ),
                accept_privacy=(
                    serializer
                    .validated_data[
                        "accept_privacy"
                    ]
                ),
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        return Response(
            {
                "accepted": True,
            },
            status=status.HTTP_200_OK,
        )
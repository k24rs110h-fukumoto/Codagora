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
    ProviderUnlinkSerializer,
)
from .auth_utils import (
    get_decoded_token,
    raise_drf_validation_error,
)
from .security_services import (
    cancel_account_deletion,
    get_firebase_security_state,
    request_account_deletion,
    revoke_all_sessions,
    unlink_provider,
)


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


class SecurityOverviewView(
    APIView,
):
    permission_classes = (
        IsAuthenticated,
    )

    def get(
        self,
        request,
    ):
        try:
            security_state = (
                get_firebase_security_state(
                    user=request.user,
                    decoded_token=(
                        get_decoded_token(
                            request
                        )
                    ),
                )
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        except firebase_exceptions.FirebaseError:
            raise FirebaseUnavailable

        return Response(
            security_state,
            status=status.HTTP_200_OK,
        )


class ProviderUnlinkView(
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
            ProviderUnlinkSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            firebase_user = (
                unlink_provider(
                    user=request.user,
                    decoded_token=(
                        get_decoded_token(
                            request
                        )
                    ),
                    provider_id=(
                        serializer
                        .validated_data[
                            "provider_id"
                        ]
                    ),
                )
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        except firebase_exceptions.FirebaseError:
            raise FirebaseUnavailable

        providers = sorted(
            {
                provider.provider_id
                for provider
                in firebase_user.provider_data
            }
        )

        return Response(
            {
                "unlinked": True,
                "providers": providers,
                "account_status": (
                    request.user
                    .account_status
                ),
            },
            status=status.HTTP_200_OK,
        )


class RevokeSessionsView(
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
        try:
            revoke_all_sessions(
                user=request.user,
                decoded_token=(
                    get_decoded_token(
                        request
                    )
                ),
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        except firebase_exceptions.FirebaseError:
            raise FirebaseUnavailable

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class AccountDeletionRequestView(
    APIView,
):
    permission_classes = (
        IsAuthenticated,
    )

    throttle_scope = (
        "account_delete"
    )

    def post(
        self,
        request,
    ):
        try:
            user = (
                request_account_deletion(
                    user=request.user,
                    decoded_token=(
                        get_decoded_token(
                            request
                        )
                    ),
                )
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        except firebase_exceptions.FirebaseError:
            raise FirebaseUnavailable

        return Response(
            {
                "account_status": (
                    user.account_status
                ),
                "deletion_scheduled_for": (
                    user
                    .deletion_scheduled_for
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class AccountDeletionCancelView(
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
        try:
            user = (
                cancel_account_deletion(
                    user=request.user,
                    decoded_token=(
                        get_decoded_token(
                            request
                        )
                    ),
                )
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        return Response(
            {
                "account_status": (
                    user.account_status
                ),
                "deletion_scheduled_for": (
                    None
                ),
            },
            status=status.HTTP_200_OK,
        )
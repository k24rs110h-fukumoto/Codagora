from django.conf import settings
from django.contrib.auth import (
    get_user_model,
)
from django.db import (
    IntegrityError,
    transaction,
)

from firebase_admin import auth
from firebase_admin import (
    exceptions as firebase_exceptions,
)

from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import (
    AuthenticationFailed,
)

from .firebase import get_firebase_app
from .models import AccountStatus


User = get_user_model()


class FirebaseAuthentication(
    BaseAuthentication,
):
    keyword = "Bearer"

    def authenticate(
        self,
        request,
    ):
        header = (
            get_authorization_header(
                request
            ).split()
        )

        if not header:
            return None

        try:
            scheme = (
                header[0]
                .decode("utf-8")
            )
        except UnicodeError as error:
            raise AuthenticationFailed(
                "Authorizationヘッダーが不正です。"
            ) from error

        if (
            scheme.lower()
            != self.keyword.lower()
        ):
            return None

        if len(header) != 2:
            raise AuthenticationFailed(
                "Bearer Tokenを正しく指定してください。"
            )

        try:
            token = (
                header[1]
                .decode("utf-8")
            )
        except UnicodeError as error:
            raise AuthenticationFailed(
                "Tokenを読み込めません。"
            ) from error

        try:
            decoded_token = (
                auth.verify_id_token(
                    token,
                    app=get_firebase_app(),
                    check_revoked=(
                        settings
                        .FIREBASE_CHECK_REVOKED
                    ),
                )
            )

        except auth.ExpiredIdTokenError as error:
            raise AuthenticationFailed(
                "認証Tokenの有効期限が切れています。"
            ) from error

        except auth.RevokedIdTokenError as error:
            raise AuthenticationFailed(
                "認証セッションが失効しています。"
            ) from error

        except auth.UserDisabledError as error:
            raise AuthenticationFailed(
                "Firebaseアカウントが無効化されています。"
            ) from error

        except (
            auth.InvalidIdTokenError,
            firebase_exceptions.FirebaseError,
            ValueError,
        ) as error:
            raise AuthenticationFailed(
                "Firebase認証に失敗しました。"
            ) from error

        firebase_uid = (
            decoded_token.get("uid")
        )

        if not firebase_uid:
            raise AuthenticationFailed(
                "Firebase UIDがありません。"
            )

        user = (
            self._get_or_provision_user(
                firebase_uid=(
                    firebase_uid
                ),
                decoded_token=(
                    decoded_token
                ),
            )
        )

        if not user.is_active:
            raise AuthenticationFailed(
                "このアカウントは無効です。"
            )

        if (
            user.account_status
            == AccountStatus.SUSPENDED
        ):
            raise AuthenticationFailed(
                "このアカウントは停止されています。"
            )

        return (
            user,
            decoded_token,
        )

    @transaction.atomic
    def _get_or_provision_user(
        self,
        *,
        firebase_uid,
        decoded_token,
    ):
        user = (
            User.objects
            .select_for_update()
            .filter(
                firebase_uid=firebase_uid,
            )
            .first()
        )

        if user:
            return user

        email = decoded_token.get(
            "email"
        )

        if email:
            email = email.strip().lower()

            email_conflict = (
                User.objects
                .filter(
                    email__iexact=email,
                )
                .exists()
            )

            if email_conflict:
                raise AuthenticationFailed(
                    "このメールアドレスは既存の"
                    "Codagoraアカウントに"
                    "関連付けられています。"
                    "既存アカウントへログインして"
                    "認証プロバイダをリンクしてください。"
                )

        firebase_claim = (
            decoded_token.get(
                "firebase"
            )
            or {}
        )

        sign_in_provider = (
            firebase_claim.get(
                "sign_in_provider"
            )
        )

        try:
            return User.objects.create_user(
                email=email,
                password=None,
                firebase_uid=(
                    firebase_uid
                ),
                email_verified=bool(
                    decoded_token.get(
                        "email_verified",
                        False,
                    )
                ),
                phone_verified=bool(
                    decoded_token.get(
                        "phone_number"
                    )
                ),
                auth_providers=(
                    [sign_in_provider]
                    if sign_in_provider
                    and sign_in_provider
                    != "anonymous"
                    else []
                ),
                is_anonymous_account=(
                    sign_in_provider
                    == "anonymous"
                ),
                account_status=(
                    AccountStatus
                    .PROVISIONAL
                ),
                display_name=(
                    decoded_token.get(
                        "name"
                    )
                    or ""
                ),
                avatar_url=(
                    decoded_token.get(
                        "picture"
                    )
                    or ""
                ),
            )

        except IntegrityError:
            user = (
                User.objects
                .filter(
                    firebase_uid=(
                        firebase_uid
                    ),
                )
                .first()
            )

            if user:
                return user

            raise AuthenticationFailed(
                "Codagoraアカウントの"
                "作成中に競合が発生しました。"
            )

    def authenticate_header(
        self,
        request,
    ):
        return self.keyword
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import (
    ValidationError,
)
from django.db import transaction
from django.utils import timezone

from firebase_admin import auth

from .auth_services import (
    sync_user_from_firebase_record,
)
from .firebase import get_firebase_app
from .models import AccountStatus


def ensure_recent_auth(
    *,
    decoded_token,
):
    auth_time = decoded_token.get(
        "auth_time"
    )

    if not isinstance(
        auth_time,
        (int, float),
    ):
        raise ValidationError(
            "再認証情報を確認できません。"
        )

    age_seconds = (
        timezone.now().timestamp()
        - float(auth_time)
    )

    if age_seconds < -60:
        raise ValidationError(
            "認証時刻が不正です。"
        )

    if (
        age_seconds
        > settings
        .CODAGORA_RECENT_AUTH_SECONDS
    ):
        raise ValidationError(
            "セキュリティ保護のため"
            "再認証してください。"
        )


def get_firebase_security_state(
    *,
    user,
    decoded_token,
):
    if not user.firebase_uid:
        raise ValidationError(
            "Firebaseアカウントが"
            "ありません。"
        )

    firebase_user = auth.get_user(
        user.firebase_uid,
        app=get_firebase_app(),
    )

    providers = sorted(
        {
            provider.provider_id
            for provider
            in firebase_user.provider_data
        }
    )

    firebase_claim = (
        decoded_token.get("firebase")
        or {}
    )

    current_provider = (
        firebase_claim.get(
            "sign_in_provider"
        )
    )

    second_factor = (
        firebase_claim.get(
            "sign_in_second_factor"
        )
    )

    provider_states = [
        {
            "provider_id": provider_id,
            "can_unlink": (
                len(providers) > 1
            ),
        }
        for provider_id in providers
    ]

    return {
        "email": firebase_user.email,
        "email_verified": bool(
            firebase_user.email_verified
        ),
        "phone_verified": bool(
            firebase_user.phone_number
        ),
        "providers": provider_states,
        "current_provider": (
            current_provider
        ),
        "mfa_used_current_session": bool(
            second_factor
        ),
        "anonymous": (
            user.is_anonymous_account
        ),
        "recent_auth_required_seconds": (
            settings
            .CODAGORA_RECENT_AUTH_SECONDS
        ),
    }


@transaction.atomic
def unlink_provider(
    *,
    user,
    decoded_token,
    provider_id,
):
    ensure_recent_auth(
        decoded_token=decoded_token,
    )

    if not user.firebase_uid:
        raise ValidationError(
            "Firebaseアカウントが"
            "ありません。"
        )

    firebase_user = auth.get_user(
        user.firebase_uid,
        app=get_firebase_app(),
    )

    providers = {
        provider.provider_id
        for provider
        in firebase_user.provider_data
    }

    if provider_id not in providers:
        raise ValidationError(
            "このログイン方法は"
            "連携されていません。"
        )

    if len(providers) <= 1:
        raise ValidationError(
            "最後のログイン方法は"
            "解除できません。"
        )

    updated_firebase_user = (
        auth.update_user(
            user.firebase_uid,
            providers_to_delete=[
                provider_id,
            ],
            app=get_firebase_app(),
        )
    )

    sync_user_from_firebase_record(
        user=user,
        firebase_user=(
            updated_firebase_user
        ),
    )

    return updated_firebase_user


def revoke_all_sessions(
    *,
    user,
    decoded_token,
):
    ensure_recent_auth(
        decoded_token=decoded_token,
    )

    if not user.firebase_uid:
        raise ValidationError(
            "Firebaseアカウントが"
            "ありません。"
        )

    auth.revoke_refresh_tokens(
        user.firebase_uid,
        app=get_firebase_app(),
    )


@transaction.atomic
def request_account_deletion(
    *,
    user,
    decoded_token,
):
    ensure_recent_auth(
        decoded_token=decoded_token,
    )

    if user.owned_workspaces.exists():
        raise ValidationError(
            "所有しているWorkspaceがあります。"
            "Workspaceを削除するか"
            "Ownerを移譲してから"
            "アカウントを削除してください。"
        )

    if (
        user.account_status
        == AccountStatus.DELETION_PENDING
    ):
        return user

    previous_status = (
        user.account_status
    )

    now = timezone.now()

    user.account_status = (
        AccountStatus.DELETION_PENDING
    )

    user.deletion_previous_status = (
        previous_status
    )

    user.deletion_requested_at = now

    user.deletion_scheduled_for = (
        now
        + timedelta(
            days=(
                settings
                .CODAGORA_ACCOUNT_DELETION_GRACE_DAYS
            )
        )
    )

    user.save(
        update_fields=(
            "account_status",
            "deletion_previous_status",
            "deletion_requested_at",
            "deletion_scheduled_for",
            "updated_at",
        )
    )

    if user.firebase_uid:
        auth.revoke_refresh_tokens(
            user.firebase_uid,
            app=get_firebase_app(),
        )

    return user


@transaction.atomic
def cancel_account_deletion(
    *,
    user,
    decoded_token,
):
    ensure_recent_auth(
        decoded_token=decoded_token,
    )

    if (
        user.account_status
        != AccountStatus.DELETION_PENDING
    ):
        raise ValidationError(
            "削除待ちのアカウント"
            "ではありません。"
        )

    previous_status = (
        user.deletion_previous_status
    )

    allowed_restore_statuses = {
        AccountStatus.PROVISIONAL,
        AccountStatus.VERIFICATION_REQUIRED,
        AccountStatus.ACTIVE,
        AccountStatus.RESTRICTED,
    }

    if (
        previous_status
        not in allowed_restore_statuses
    ):
        if (
            user.onboarding_completed_at
            and user.email
            and user.email_verified
        ):
            previous_status = (
                AccountStatus.ACTIVE
            )
        else:
            previous_status = (
                AccountStatus.PROVISIONAL
            )

    user.account_status = (
        previous_status
    )

    user.deletion_previous_status = None
    user.deletion_requested_at = None
    user.deletion_scheduled_for = None

    user.save(
        update_fields=(
            "account_status",
            "deletion_previous_status",
            "deletion_requested_at",
            "deletion_scheduled_for",
            "updated_at",
        )
    )

    return user
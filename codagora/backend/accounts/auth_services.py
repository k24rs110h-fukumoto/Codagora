import re

from django.conf import settings
from django.core.exceptions import (
    ValidationError,
)
from django.db import transaction
from django.utils import timezone

from firebase_admin import auth

from .firebase import get_firebase_app
from .models import (
    AccountStatus,
    LegalDocumentAcceptance,
    LegalDocumentType,
    User,
)


def get_sign_in_provider(
    decoded_token,
):
    firebase_claim = (
        decoded_token.get("firebase")
        or {}
    )

    return firebase_claim.get(
        "sign_in_provider"
    )


def get_current_session_mfa(
    decoded_token,
):
    firebase_claim = (
        decoded_token.get("firebase")
        or {}
    )

    return bool(
        firebase_claim.get(
            "sign_in_second_factor"
        )
    )


def has_current_legal_acceptance(
    *,
    user,
    document_type,
    version,
):
    return (
        LegalDocumentAcceptance
        .objects
        .filter(
            user=user,
            document_type=(
                document_type
            ),
            version=version,
        )
        .exists()
    )


def sync_user_from_firebase_record(
    *,
    user,
    firebase_user,
):
    firebase_email = (
        firebase_user.email
    )

    if firebase_email:
        firebase_email = (
            firebase_email
            .strip()
            .lower()
        )

        conflict = (
            User.objects
            .filter(
                email__iexact=(
                    firebase_email
                ),
            )
            .exclude(
                pk=user.pk,
            )
            .exists()
        )

        if conflict:
            raise ValidationError(
                "Firebaseのメールアドレスが"
                "別のCodagoraアカウントで"
                "使用されています。"
            )

    providers = sorted(
        {
            provider.provider_id
            for provider
            in firebase_user.provider_data
        }
    )

    user.email = firebase_email

    user.email_verified = bool(
        firebase_user.email_verified
    )

    user.phone_verified = bool(
        firebase_user.phone_number
    )

    user.auth_providers = providers

    user.is_anonymous_account = (
        len(providers) == 0
        and not firebase_user.email
        and not firebase_user.phone_number
    )

    if (
        not user.display_name
        and firebase_user.display_name
    ):
        user.display_name = (
            firebase_user.display_name
        )

    if (
        not user.avatar_url
        and firebase_user.photo_url
    ):
        user.avatar_url = (
            firebase_user.photo_url
        )

    if (
        user.account_status
        == AccountStatus.ACTIVE
        and (
            not user.email
            or not user.email_verified
            or user.is_anonymous_account
        )
    ):
        user.account_status = (
            AccountStatus
            .VERIFICATION_REQUIRED
        )

    user.save(
        update_fields=(
            "email",
            "email_verified",
            "phone_verified",
            "auth_providers",
            "is_anonymous_account",
            "display_name",
            "avatar_url",
            "account_status",
            "updated_at",
        )
    )

    return user


@transaction.atomic
def sync_firebase_user(
    *,
    user,
    decoded_token,
):
    if not user.firebase_uid:
        raise ValidationError(
            "Firebase UIDがありません。"
        )

    firebase_user = auth.get_user(
        user.firebase_uid,
        app=get_firebase_app(),
    )

    sync_user_from_firebase_record(
        user=user,
        firebase_user=firebase_user,
    )

    return firebase_user


def build_onboarding_requirements(
    *,
    user,
    decoded_token,
):
    terms_version = (
        settings
        .CODAGORA_TERMS_VERSION
    )

    privacy_version = (
        settings
        .CODAGORA_PRIVACY_VERSION
    )

    terms_accepted = (
        has_current_legal_acceptance(
            user=user,
            document_type=(
                LegalDocumentType.TERMS
            ),
            version=terms_version,
        )
    )

    privacy_accepted = (
        has_current_legal_acceptance(
            user=user,
            document_type=(
                LegalDocumentType.PRIVACY
            ),
            version=privacy_version,
        )
    )

    profile_complete = bool(
        user.display_name
        and user.handle
    )

    return {
        "profile_complete": (
            profile_complete
        ),
        "email_present": bool(
            user.email
        ),
        "email_verified": (
            user.email_verified
        ),
        "phone_verified": (
            user.phone_verified
        ),
        "phone_recommended": (
            not user.phone_verified
        ),
        "terms_accepted": (
            terms_accepted
        ),
        "privacy_accepted": (
            privacy_accepted
        ),
        "legal_reacceptance_required": (
            not terms_accepted
            or not privacy_accepted
        ),
        "anonymous_upgrade_required": (
            user.is_anonymous_account
        ),
        "mfa_used_current_session": (
            get_current_session_mfa(
                decoded_token
            )
        ),
        "sign_in_provider": (
            get_sign_in_provider(
                decoded_token
            )
        ),
    }


def validate_handle(
    handle,
):
    normalized = (
        handle
        .strip()
        .lower()
    )

    if not re.fullmatch(
        r"[a-z0-9_]{3,30}",
        normalized,
    ):
        raise ValidationError(
            "handleは3〜30文字の"
            "英小文字・数字・_のみ"
            "使用できます。"
        )

    return normalized


def accept_current_legal_documents(
    *,
    user,
    accept_terms,
    accept_privacy,
):
    if not accept_terms:
        raise ValidationError(
            "利用規約への同意が必要です。"
        )

    if not accept_privacy:
        raise ValidationError(
            "プライバシーポリシーへの"
            "同意が必要です。"
        )

    LegalDocumentAcceptance.objects.get_or_create(
        user=user,
        document_type=(
            LegalDocumentType.TERMS
        ),
        version=(
            settings
            .CODAGORA_TERMS_VERSION
        ),
    )

    LegalDocumentAcceptance.objects.get_or_create(
        user=user,
        document_type=(
            LegalDocumentType.PRIVACY
        ),
        version=(
            settings
            .CODAGORA_PRIVACY_VERSION
        ),
    )


@transaction.atomic
def complete_onboarding(
    *,
    user,
    decoded_token,
    display_name,
    handle,
    accept_terms,
    accept_privacy,
):
    if user.account_status not in (
        AccountStatus.PROVISIONAL,
        AccountStatus.VERIFICATION_REQUIRED,
    ):
        raise ValidationError(
            "現在のアカウント状態では"
            "初期登録を実行できません。"
        )

    sync_firebase_user(
        user=user,
        decoded_token=decoded_token,
    )

    if user.is_anonymous_account:
        raise ValidationError(
            "匿名アカウントのままでは"
            "登録を完了できません。"
        )

    if not user.email:
        raise ValidationError(
            "メールアドレスを"
            "Firebaseアカウントへ"
            "追加してください。"
        )

    if not user.email_verified:
        raise ValidationError(
            "メールアドレスの確認を"
            "完了してください。"
        )

    normalized_display_name = (
        display_name.strip()
    )

    if not normalized_display_name:
        raise ValidationError(
            "表示名を入力してください。"
        )

    normalized_handle = (
        validate_handle(handle)
    )

    handle_conflict = (
        User.objects
        .filter(
            handle__iexact=(
                normalized_handle
            ),
        )
        .exclude(
            pk=user.pk,
        )
        .exists()
    )

    if handle_conflict:
        raise ValidationError(
            "このhandleは"
            "すでに使用されています。"
        )

    accept_current_legal_documents(
        user=user,
        accept_terms=accept_terms,
        accept_privacy=accept_privacy,
    )

    user.display_name = (
        normalized_display_name
    )

    user.handle = (
        normalized_handle
    )

    user.account_status = (
        AccountStatus.ACTIVE
    )

    user.onboarding_completed_at = (
        timezone.now()
    )

    user.save(
        update_fields=(
            "display_name",
            "handle",
            "account_status",
            "onboarding_completed_at",
            "updated_at",
        )
    )

    return user
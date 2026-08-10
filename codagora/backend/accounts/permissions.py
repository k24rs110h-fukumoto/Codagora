from rest_framework.permissions import (
    BasePermission,
)

from .models import AccountStatus


class IsActiveCodagoraUser(
    BasePermission,
):
    message = (
        "Codagoraアカウントの"
        "初期設定または本人確認が"
        "完了していません。"
    )

    def has_permission(
        self,
        request,
        view,
    ):
        user = request.user

        if (
            not user
            or not user.is_authenticated
        ):
            return False

        if (
            user.is_staff
            or user.is_superuser
        ):
            return True

        return (
            user.is_active
            and user.account_status
            == AccountStatus.ACTIVE
        )
from django.contrib import admin
from django.contrib.auth.admin import (
    UserAdmin as BaseUserAdmin,
)

from .models import (
    LegalDocumentAcceptance,
    Skill,
    User,
    UserFollow,
    UserSkill,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = (
        "email",
    )

    list_display = (
        "email",
        "display_name",
        "handle",
        "account_status",
        "email_verified",
        "phone_verified",
        "availability",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "email",
        "display_name",
        "handle",
        "firebase_uid",
    )

    list_filter = (
        "account_status",
        "email_verified",
        "phone_verified",
        "is_anonymous_account",
        "availability",
        "is_profile_public",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                ),
            },
        ),
        (
            "Codagoraアカウント",
            {
                "fields": (
                    "account_status",
                    "onboarding_completed_at",
                    "deletion_previous_status",
                    "deletion_requested_at",
                    "deletion_scheduled_for",
                ),
            },
        ),
        (
            "プロフィール",
            {
                "fields": (
                    "display_name",
                    "handle",
                    "avatar_url",
                    "headline",
                    "bio",
                    "location_name",
                    "website_url",
                    "github_username",
                    "availability",
                    "timezone",
                    "is_profile_public",
                    "last_active_at",
                ),
            },
        ),
        (
            "Firebase Authentication",
            {
                "fields": (
                    "firebase_uid",
                    "email_verified",
                    "phone_verified",
                    "auth_providers",
                    "is_anonymous_account",
                ),
            },
        ),
        (
            "権限",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "日時",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "updated_at",
                ),
            },
        ),
    )

    readonly_fields = (
        "firebase_uid",
        "email_verified",
        "phone_verified",
        "auth_providers",
        "is_anonymous_account",
        "onboarding_completed_at",
        "deletion_previous_status",
        "deletion_requested_at",
        "deletion_scheduled_for",
        "last_active_at",
        "updated_at",
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "display_name",
                    "account_status",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):
        fields = list(
            self.readonly_fields
        )

        if (
            obj
            and obj.firebase_uid
        ):
            fields.append(
                "email"
            )

        return tuple(fields)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created_at",
    )

    search_fields = (
        "name",
    )

    readonly_fields = (
        "id",
        "created_at",
    )


@admin.register(UserSkill)
class UserSkillAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "user",
        "skill",
        "level",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__display_name",
        "user__handle",
        "skill__name",
    )

    list_filter = (
        "level",
    )

    autocomplete_fields = (
        "user",
        "skill",
    )

    readonly_fields = (
        "id",
        "created_at",
    )


@admin.register(UserFollow)
class UserFollowAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "follower",
        "following",
        "created_at",
    )

    search_fields = (
        "follower__email",
        "follower__display_name",
        "follower__handle",
        "following__email",
        "following__display_name",
        "following__handle",
    )

    autocomplete_fields = (
        "follower",
        "following",
    )

    readonly_fields = (
        "id",
        "created_at",
    )

    ordering = (
        "-created_at",
    )


@admin.register(
    LegalDocumentAcceptance
)
class LegalDocumentAcceptanceAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "user",
        "document_type",
        "version",
        "accepted_at",
    )

    search_fields = (
        "user__email",
        "user__display_name",
        "user__handle",
        "version",
    )

    list_filter = (
        "document_type",
        "version",
        "accepted_at",
    )

    autocomplete_fields = (
        "user",
    )

    readonly_fields = (
        "id",
        "user",
        "document_type",
        "version",
        "accepted_at",
    )

    ordering = (
        "-accepted_at",
    )

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False
from django.core.exceptions import (
    ValidationError,
)
from django.db import transaction

from .models import DeveloperProfile


def normalize_string_list(
    value,
    *,
    maximum_items=20,
    maximum_length=50,
):
    if value is None:
        return []

    if not isinstance(
        value,
        (list, tuple),
    ):
        raise ValidationError(
            "リスト形式で指定してください。"
        )

    result = []
    seen = set()

    for item in value:
        item = str(
            item
        ).strip()

        if not item:
            continue

        if len(item) > maximum_length:
            raise ValidationError(
                f"各項目は{maximum_length}文字以内"
                "で指定してください。"
            )

        normalized_key = (
            item.lower()
        )

        if normalized_key in seen:
            continue

        seen.add(
            normalized_key
        )

        result.append(
            item
        )

    if len(result) > maximum_items:
        raise ValidationError(
            f"最大{maximum_items}件までです。"
        )

    return result


def get_or_create_developer_profile(
    *,
    user,
):
    profile, _ = (
        DeveloperProfile.objects
        .get_or_create(
            user=user,
        )
    )

    return profile


@transaction.atomic
def update_developer_profile(
    *,
    user,
    data,
):
    profile = (
        DeveloperProfile.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            user=user,
        )
        .first()
    )

    if profile is None:
        profile = (
            DeveloperProfile.objects
            .create(
                user=user,
            )
        )

    text_fields = (
        "headline",
        "bio",
        "location_label",
    )

    for field in text_fields:
        if field not in data:
            continue

        value = data[
            field
        ].strip()

        setattr(
            profile,
            field,
            value,
        )

    url_fields = (
        "website_url",
        "portfolio_url",
        "github_url",
    )

    for field in url_fields:
        if field not in data:
            continue

        setattr(
            profile,
            field,
            data[field],
        )

    if "skills" in data:
        profile.skills = (
            normalize_string_list(
                data[
                    "skills"
                ],
                maximum_items=30,
            )
        )

    if "interests" in data:
        profile.interests = (
            normalize_string_list(
                data[
                    "interests"
                ],
                maximum_items=20,
            )
        )

    if "looking_for" in data:
        profile.looking_for = (
            normalize_string_list(
                data[
                    "looking_for"
                ],
                maximum_items=10,
            )
        )

    if "availability" in data:
        availability = data[
            "availability"
        ]

        if (
            availability
            not in DeveloperProfile
            .Availability
            .values
        ):
            raise ValidationError(
                "Availabilityが不正です。"
            )

        profile.availability = (
            availability
        )

    for field in (
        "is_public",
        "show_projects",
        "show_activity",
    ):
        if field in data:
            setattr(
                profile,
                field,
                bool(
                    data[field]
                ),
            )

    profile.save()

    return profile
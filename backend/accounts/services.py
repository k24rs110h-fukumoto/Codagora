from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import (
    Skill,
    UserFollow,
    UserSkill,
)


User = get_user_model()


@transaction.atomic
def set_user_skill(
    *,
    user,
    name: str,
    level: int,
) -> UserSkill:
    normalized_name = " ".join(
        name.strip().split()
    )

    if not normalized_name:
        raise ValidationError(
            "スキル名を入力してください。"
        )

    if level < 1 or level > 5:
        raise ValidationError(
            "スキルレベルは1〜5で指定してください。"
        )

    skill = Skill.objects.filter(
        name__iexact=normalized_name,
    ).first()

    if skill is None:
        try:
            skill = Skill.objects.create(
                name=normalized_name,
            )
        except IntegrityError:
            skill = Skill.objects.get(
                name__iexact=normalized_name,
            )

    user_skill, _ = (
        UserSkill.objects.update_or_create(
            user=user,
            skill=skill,
            defaults={
                "level": level,
            },
        )
    )

    return user_skill


@transaction.atomic
def update_user_skill_level(
    *,
    user_skill: UserSkill,
    user,
    level: int,
) -> UserSkill:
    if user_skill.user_id != user.id:
        raise ValidationError(
            "このスキルを変更できません。"
        )

    if level < 1 or level > 5:
        raise ValidationError(
            "スキルレベルは1〜5で指定してください。"
        )

    user_skill.level = level

    user_skill.save(
        update_fields=(
            "level",
        )
    )

    return user_skill


@transaction.atomic
def follow_user(
    *,
    follower,
    following,
):
    if follower.id == following.id:
        raise ValidationError(
            "自分自身をフォローできません。"
        )

    return UserFollow.objects.get_or_create(
        follower=follower,
        following=following,
    )


@transaction.atomic
def unfollow_user(
    *,
    follower,
    following,
):
    UserFollow.objects.filter(
        follower=follower,
        following=following,
    ).delete()
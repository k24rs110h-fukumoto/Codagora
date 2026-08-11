from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def normalize_codagora_email(
        self,
        email,
    ):
        if not email:
            return None

        return self.normalize_email(
            email.strip()
        ).lower()

    def _create_user(
        self,
        email=None,
        password=None,
        **extra_fields,
    ):
        email = self.normalize_codagora_email(
            email
        )

        user = self.model(
            email=email,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(
            using=self._db,
        )

        return user

    def create_user(
        self,
        email=None,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault(
            "is_staff",
            False,
        )

        extra_fields.setdefault(
            "is_superuser",
            False,
        )

        extra_fields.setdefault(
            "is_active",
            True,
        )

        extra_fields.setdefault(
            "account_status",
            "active",
        )

        return self._create_user(
            email=email,
            password=password,
            **extra_fields,
        )

    def create_superuser(
        self,
        email,
        password=None,
        **extra_fields,
    ):
        if not email:
            raise ValueError(
                "Superuserにはメールアドレスが必要です。"
            )

        extra_fields.setdefault(
            "is_staff",
            True,
        )

        extra_fields.setdefault(
            "is_superuser",
            True,
        )

        extra_fields.setdefault(
            "is_active",
            True,
        )

        extra_fields.setdefault(
            "account_status",
            "active",
        )

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "Superuserはis_staff=Trueである必要があります。"
            )

        if (
            extra_fields.get("is_superuser")
            is not True
        ):
            raise ValueError(
                "Superuserはis_superuser=Trueである必要があります。"
            )

        return self._create_user(
            email=email,
            password=password,
            **extra_fields,
        )
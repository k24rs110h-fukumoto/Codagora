from django.apps import AppConfig


class WorkspaceFilesConfig(AppConfig):
    default_auto_field = (
        "django.db.models.BigAutoField"
    )

    name = "workspace_files"

    def ready(self):
        from . import signals  # noqa: F401
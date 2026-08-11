import firebase_admin

from django.conf import settings


def get_firebase_app():
    try:
        return firebase_admin.get_app()

    except ValueError:
        project_id = getattr(
            settings,
            "FIREBASE_PROJECT_ID",
            "",
        )

        if project_id:
            return (
                firebase_admin.initialize_app(
                    options={
                        "projectId": project_id,
                    }
                )
            )

        return (
            firebase_admin.initialize_app()
        )
from django.urls import path

from .auth_views import (
    AuthBootstrapView,
    LegalAcceptanceView,
    OnboardingCompleteView,
)
from .security_views import (
    AccountDeletionCancelView,
    AccountDeletionRequestView,
    ProviderUnlinkView,
    RevokeSessionsView,
    SecurityOverviewView,
)


app_name = "auth"


urlpatterns = [
    path(
        "bootstrap/",
        AuthBootstrapView.as_view(),
        name="bootstrap",
    ),

    path(
        "onboarding/complete/",
        OnboardingCompleteView.as_view(),
        name="onboarding-complete",
    ),

    path(
        "legal/accept/",
        LegalAcceptanceView.as_view(),
        name="legal-accept",
    ),

    path(
        "security/",
        SecurityOverviewView.as_view(),
        name="security",
    ),

    path(
        "security/providers/unlink/",
        ProviderUnlinkView.as_view(),
        name="provider-unlink",
    ),

    path(
        "sessions/revoke/",
        RevokeSessionsView.as_view(),
        name="revoke-sessions",
    ),

    path(
        "account/deletion/request/",
        AccountDeletionRequestView.as_view(),
        name="account-deletion-request",
    ),

    path(
        "account/deletion/cancel/",
        AccountDeletionCancelView.as_view(),
        name="account-deletion-cancel",
    ),
]
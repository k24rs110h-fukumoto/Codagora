from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse

from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import AccountStatus
from locations.models import (
    WorkspaceLocationShare,
    WorkspacePlace,
)
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class LocationShareApiTests(
    APITestCase,
):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="share-owner@example.com",
            password=None,
            firebase_uid="share-owner",
            display_name="Owner",
            handle="share_owner",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.member = User.objects.create_user(
            email="share-member@example.com",
            password=None,
            firebase_uid="share-member",
            display_name="Member",
            handle="share_member",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.guest = User.objects.create_user(
            email="share-guest@example.com",
            password=None,
            firebase_uid="share-guest",
            display_name="Guest",
            handle="share_guest",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.workspace = create_workspace(
            owner=self.owner,
            name="Share Workspace",
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=(
                WorkspaceMember.Role.MEMBER
            ),
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.guest,
            role=(
                WorkspaceMember.Role.GUEST
            ),
        )

        self.place = (
            WorkspacePlace.objects.create(
                workspace=self.workspace,
                name="Campus",
                latitude="33.670000",
                longitude="130.440000",
                created_by=self.owner,
            )
        )

    def shares_url(self):
        return reverse(
            "workspaces:locations:"
            "location-share-list-create",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def current_url(self):
        return reverse(
            "workspaces:locations:"
            "current-location-share",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def test_member_can_share_coordinates(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.shares_url(),
            {
                "label": "Working",
                "note": "Until evening",
                "latitude": (
                    "33.590000"
                ),
                "longitude": (
                    "130.401000"
                ),
                "duration_minutes": 120,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            WorkspaceLocationShare.objects
            .filter(
                workspace=self.workspace,
                user=self.member,
                ended_at__isnull=True,
            )
            .count(),
            1,
        )

    def test_member_can_share_saved_place(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.shares_url(),
            {
                "place_id": (
                    str(self.place.id)
                ),
                "duration_minutes": 60,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        share = (
            WorkspaceLocationShare.objects
            .get(
                id=response.data["id"]
            )
        )

        self.place.refresh_from_db()

        self.assertEqual(
            share.place_id,
            self.place.id,
        )

        self.assertEqual(
            share.latitude,
            self.place.latitude,
        )

        self.assertEqual(
            share.longitude,
            self.place.longitude,
        )

    def test_new_share_closes_previous_share(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        first = self.client.post(
            self.shares_url(),
            {
                "latitude": "33.500000",
                "longitude": "130.400000",
            },
            format="json",
        )

        second = self.client.post(
            self.shares_url(),
            {
                "latitude": "33.600000",
                "longitude": "130.500000",
            },
            format="json",
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            WorkspaceLocationShare.objects
            .filter(
                workspace=self.workspace,
                user=self.member,
                ended_at__isnull=True,
            )
            .count(),
            1,
        )

        first_share = (
            WorkspaceLocationShare.objects
            .get(
                id=first.data["id"]
            )
        )

        self.assertIsNotNone(
            first_share.ended_at
        )

    def test_member_can_stop_sharing(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        self.client.post(
            self.shares_url(),
            {
                "latitude": "33.500000",
                "longitude": "130.400000",
            },
            format="json",
        )

        response = self.client.delete(
            self.current_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            WorkspaceLocationShare.objects
            .filter(
                workspace=self.workspace,
                user=self.member,
                ended_at__isnull=True,
            )
            .exists()
        )

    def test_guest_cannot_share_location(
        self,
    ):
        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.post(
            self.shares_url(),
            {
                "latitude": "33.500000",
                "longitude": "130.400000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_guest_cannot_view_member_locations(
        self,
    ):
        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.get(
            self.shares_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_current_endpoint_reports_no_share(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.get(
            self.current_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            response.data["sharing"]
        )

        self.assertIsNone(
            response.data["share"]
        )

    def test_duration_over_limit_rejected(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.shares_url(),
            {
                "latitude": "33.500000",
                "longitude": "130.400000",
                "duration_minutes": 2000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
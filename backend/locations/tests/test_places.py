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
    WorkspacePlace,
)
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class WorkspacePlaceApiTests(
    APITestCase,
):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="map-owner@example.com",
            password=None,
            firebase_uid="map-owner",
            display_name="Owner",
            handle="map_owner",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.member = User.objects.create_user(
            email="map-member@example.com",
            password=None,
            firebase_uid="map-member",
            display_name="Member",
            handle="map_member",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.member2 = User.objects.create_user(
            email="map-member2@example.com",
            password=None,
            firebase_uid="map-member2",
            display_name="Member2",
            handle="map_member2",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.guest = User.objects.create_user(
            email="map-guest@example.com",
            password=None,
            firebase_uid="map-guest",
            display_name="Guest",
            handle="map_guest",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.workspace = create_workspace(
            owner=self.owner,
            name="Map Workspace",
        )

        for user, role in (
            (
                self.member,
                WorkspaceMember.Role.MEMBER,
            ),
            (
                self.member2,
                WorkspaceMember.Role.MEMBER,
            ),
            (
                self.guest,
                WorkspaceMember.Role.GUEST,
            ),
        ):
            WorkspaceMember.objects.create(
                workspace=self.workspace,
                user=user,
                role=role,
            )

    def list_url(self):
        return reverse(
            "workspaces:locations:"
            "place-list-create",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def test_member_can_create_place(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.list_url(),
            {
                "name": "University",
                "description": (
                    "Working space"
                ),
                "address": (
                    "Fukuoka"
                ),
                "latitude": (
                    "33.590000"
                ),
                "longitude": (
                    "130.401000"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            WorkspacePlace.objects.filter(
                workspace=self.workspace,
                name="University",
            ).exists()
        )

    def test_guest_cannot_create_place(
        self,
    ):
        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.post(
            self.list_url(),
            {
                "name": "Invalid",
                "latitude": "33.5",
                "longitude": "130.4",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_guest_can_view_places(
        self,
    ):
        WorkspacePlace.objects.create(
            workspace=self.workspace,
            name="Office",
            latitude="33.500000",
            longitude="130.400000",
            created_by=self.owner,
        )

        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_invalid_latitude_is_rejected(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.list_url(),
            {
                "name": "Invalid",
                "latitude": "91.000000",
                "longitude": "130.000000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_creator_can_update_place(
        self,
    ):
        place = WorkspacePlace.objects.create(
            workspace=self.workspace,
            name="Old",
            latitude="33.500000",
            longitude="130.400000",
            created_by=self.member,
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.patch(
            reverse(
                "workspaces:locations:"
                "place-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "place_id": place.id,
                },
            ),
            {
                "name": "New",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        place.refresh_from_db()

        self.assertEqual(
            place.name,
            "New",
        )

    def test_other_member_cannot_edit_place(
        self,
    ):
        place = WorkspacePlace.objects.create(
            workspace=self.workspace,
            name="Place",
            latitude="33.500000",
            longitude="130.400000",
            created_by=self.member,
        )

        self.client.force_authenticate(
            user=self.member2,
        )

        response = self.client.patch(
            reverse(
                "workspaces:locations:"
                "place-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "place_id": place.id,
                },
            ),
            {
                "name": "Changed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_owner_can_delete_place(
        self,
    ):
        place = WorkspacePlace.objects.create(
            workspace=self.workspace,
            name="Place",
            latitude="33.500000",
            longitude="130.400000",
            created_by=self.member,
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.delete(
            reverse(
                "workspaces:locations:"
                "place-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "place_id": place.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        place.refresh_from_db()

        self.assertIsNotNone(
            place.deleted_at
        )
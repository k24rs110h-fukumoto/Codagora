from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import AccountStatus
from scheduling.models import (
    CalendarEvent,
    CalendarEventParticipant,
    ParticipantResponse,
)
from workspaces.models import WorkspaceMember
from workspaces.services import create_workspace


User = get_user_model()


class CalendarEventApiTests(
    APITestCase,
):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="calendar-owner@example.com",
            password=None,
            firebase_uid="calendar-owner",
            display_name="Owner",
            handle="calendar_owner",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.member = User.objects.create_user(
            email="calendar-member@example.com",
            password=None,
            firebase_uid="calendar-member",
            display_name="Member",
            handle="calendar_member",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.guest = User.objects.create_user(
            email="calendar-guest@example.com",
            password=None,
            firebase_uid="calendar-guest",
            display_name="Guest",
            handle="calendar_guest",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.workspace = create_workspace(
            owner=self.owner,
            name="Calendar Workspace",
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

    def list_url(self):
        return reverse(
            "workspaces:scheduling:"
            "event-list-create",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def test_member_can_create_event(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.list_url(),
            {
                "title": "Meeting",
                "timezone": "Asia/Tokyo",
                "is_all_day": False,
                "starts_at": (
                    "2026-08-10T10:00:00+09:00"
                ),
                "ends_at": (
                    "2026-08-10T11:00:00+09:00"
                ),
                "participant_ids": [
                    str(self.guest.id),
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        event = CalendarEvent.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            event.created_by_id,
            self.member.id,
        )

        self.assertTrue(
            CalendarEventParticipant.objects.filter(
                event=event,
                user=self.member,
                response=(
                    ParticipantResponse.ACCEPTED
                ),
            ).exists()
        )

        self.assertTrue(
            CalendarEventParticipant.objects.filter(
                event=event,
                user=self.guest,
            ).exists()
        )

    def test_guest_cannot_create_event(
        self,
    ):
        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.post(
            self.list_url(),
            {
                "title": "Invalid",
                "is_all_day": True,
                "start_date": "2026-08-10",
                "end_date": "2026-08-10",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_all_day_event_can_be_created(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            self.list_url(),
            {
                "title": "Hackathon",
                "is_all_day": True,
                "start_date": "2026-08-10",
                "end_date": "2026-08-12",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            response.data[
                "is_all_day"
            ]
        )

    def test_invalid_period_is_rejected(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.list_url(),
            {
                "title": "Invalid",
                "is_all_day": False,
                "starts_at": (
                    "2026-08-10T12:00:00+09:00"
                ),
                "ends_at": (
                    "2026-08-10T10:00:00+09:00"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_participant_can_respond(
        self,
    ):
        event = CalendarEvent.objects.create(
            workspace=self.workspace,
            title="Meeting",
            created_by=self.owner,
            is_all_day=True,
            start_date="2026-08-10",
            end_date="2026-08-10",
        )

        CalendarEventParticipant.objects.create(
            event=event,
            user=self.member,
            added_by=self.owner,
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            reverse(
                "workspaces:scheduling:"
                "participant-response",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "event_id": event.id,
                },
            ),
            {
                "response": "accepted",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        participant = (
            CalendarEventParticipant
            .objects
            .get(
                event=event,
                user=self.member,
            )
        )

        self.assertEqual(
            participant.response,
            ParticipantResponse.ACCEPTED,
        )

    def test_creator_can_soft_delete_event(
        self,
    ):
        event = CalendarEvent.objects.create(
            workspace=self.workspace,
            title="Delete",
            created_by=self.member,
            is_all_day=True,
            start_date="2026-08-10",
            end_date="2026-08-10",
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.delete(
            reverse(
                "workspaces:scheduling:"
                "event-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "event_id": event.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        event.refresh_from_db()

        self.assertIsNotNone(
            event.deleted_at
        )
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.dateparse import (
    parse_datetime,
)

from accounts.models import AccountStatus
from scheduling.models import (
    CalendarEvent,
    RecurrenceFrequency,
)
from scheduling.recurrence import (
    expand_event_occurrences,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class CalendarRecurrenceTests(
    TestCase,
):
    def setUp(self):
        self.user = User.objects.create_user(
            email="repeat@example.com",
            password=None,
            firebase_uid="repeat-user",
            display_name="Repeat",
            handle="repeat_user",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.workspace = (
            create_workspace(
                owner=self.user,
                name="Repeat Workspace",
            )
        )

    def test_daily_recurrence(
        self,
    ):
        event = CalendarEvent.objects.create(
            workspace=self.workspace,
            title="Daily",
            created_by=self.user,
            timezone="Asia/Tokyo",
            is_all_day=True,
            start_date=date(
                2026,
                8,
                1,
            ),
            end_date=date(
                2026,
                8,
                1,
            ),
            recurrence_frequency=(
                RecurrenceFrequency.DAILY
            ),
            recurrence_interval=2,
            recurrence_until=date(
                2026,
                8,
                10,
            ),
        )

        occurrences = (
            expand_event_occurrences(
                event=event,
                range_start=date(
                    2026,
                    8,
                    1,
                ),
                range_end=date(
                    2026,
                    8,
                    10,
                ),
            )
        )

        dates = [
            item["start_date"]
            for item
            in occurrences
        ]

        self.assertEqual(
            dates,
            [
                date(2026, 8, 1),
                date(2026, 8, 3),
                date(2026, 8, 5),
                date(2026, 8, 7),
                date(2026, 8, 9),
            ],
        )

    def test_weekly_recurrence(
        self,
    ):
        event = CalendarEvent.objects.create(
            workspace=self.workspace,
            title="Weekly",
            created_by=self.user,
            timezone="Asia/Tokyo",
            is_all_day=True,
            start_date=date(
                2026,
                8,
                3,
            ),
            end_date=date(
                2026,
                8,
                3,
            ),
            recurrence_frequency=(
                RecurrenceFrequency.WEEKLY
            ),
            recurrence_interval=1,
            recurrence_weekdays=[
                0,
                2,
            ],
            recurrence_until=date(
                2026,
                8,
                16,
            ),
        )

        occurrences = (
            expand_event_occurrences(
                event=event,
                range_start=date(
                    2026,
                    8,
                    3,
                ),
                range_end=date(
                    2026,
                    8,
                    16,
                ),
            )
        )

        dates = [
            item["start_date"]
            for item
            in occurrences
        ]

        self.assertEqual(
            dates,
            [
                date(2026, 8, 3),
                date(2026, 8, 5),
                date(2026, 8, 10),
                date(2026, 8, 12),
            ],
        )

    def test_timed_recurrence(
        self,
    ):
        event = CalendarEvent.objects.create(
            workspace=self.workspace,
            title="Timed",
            created_by=self.user,
            timezone="Asia/Tokyo",
            is_all_day=False,
            starts_at=parse_datetime(
                "2026-08-01T10:00:00+09:00"
            ),
            ends_at=parse_datetime(
                "2026-08-01T11:00:00+09:00"
            ),
            recurrence_frequency=(
                RecurrenceFrequency.DAILY
            ),
            recurrence_interval=1,
            recurrence_until=date(
                2026,
                8,
                3,
            ),
        )

        occurrences = (
            expand_event_occurrences(
                event=event,
                range_start=date(
                    2026,
                    8,
                    1,
                ),
                range_end=date(
                    2026,
                    8,
                    3,
                ),
            )
        )

        self.assertEqual(
            len(occurrences),
            3,
        )
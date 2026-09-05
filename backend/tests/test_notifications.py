"""When the reminder loop is allowed to speak.

The hour is the only rule that is pure - everything else about reminders needs the
database - and it is the one that decides whether a user is woken at 03:00.
"""
from datetime import datetime

from app.core.config import settings
from app.services.notifications import is_within_sending_hours


def test_nothing_is_sent_before_the_configured_hour():
    too_early = datetime(2026, 9, 3, settings.NOTIFICATIONS_HOUR - 1, 59)

    assert not is_within_sending_hours(too_early)


def test_the_configured_hour_itself_counts_as_allowed():
    """A window that opens strictly after its hour skips the whole first tick."""
    assert is_within_sending_hours(datetime(2026, 9, 3, settings.NOTIFICATIONS_HOUR, 0))


def test_later_in_the_day_is_still_allowed():
    """An app started in the afternoon has to catch up, not wait until tomorrow."""
    assert is_within_sending_hours(datetime(2026, 9, 3, 23, 30))

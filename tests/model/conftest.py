"""Fixtures for model tests."""

import pytest
from datetime import date, time

from model.calendar import Calendar, Event, Day, Category, Occurrence


@pytest.fixture
def mock_event():
    """Create a mock event for testing."""
    return Event(
        title="Test Event",
        emoji="🎉",
        description="This is a test event",
        category=Category.GENERAL,
        occurrence=Occurrence.WITHIN_DAY,
        date=date.today(),
        time=time(14, 30),
        venue="Test Venue",
        location="https://maps.google.com/?q=Test+Location",
        url="https://example.com",
    )


@pytest.fixture
def mock_recurring_event():
    """Create a mock recurring event for testing."""
    event = Event(
        title="Recurring Test Event",
        emoji="🔄",
        description="This is a regular test event",
        occurrence=Occurrence.REGULAR,
        days={Day.Monday, Day.Wednesday, Day.Friday},
        time=time(18, 0),
        venue="Standard Venue",
    )
    return event


@pytest.fixture
def calendar():
    """Create a calendar instance for testing."""
    return Calendar()

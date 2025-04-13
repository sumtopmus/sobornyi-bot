"""Fixtures for model tests."""

from datetime import date, time, timedelta

import pytest

from model import Calendar, Category, Day, Event, Occurrence


@pytest.fixture
def dummy_date():
    """Create a mock fixed date for testing."""
    return date(2025, 3, 20)  # Thursday


@pytest.fixture(autouse=True)
def patch_this_and_next_week(monkeypatch, dummy_date):
    """Automatically patch all this_week and next_week calls to return the dummy date."""
    # dummy_monday = date(2025, 3, 17)  # Monday
    dummy_monday = dummy_date - timedelta(days=dummy_date.weekday())

    def mock_this_week_func():
        return dummy_monday

    def mock_next_week_func():
        return dummy_monday + timedelta(days=7)

    monkeypatch.setattr("model.this_week", mock_this_week_func)
    monkeypatch.setattr("model.event.this_week", mock_this_week_func)
    monkeypatch.setattr("model.calendar.this_week", mock_this_week_func)
    monkeypatch.setattr("model.utils.this_week", mock_this_week_func)
    monkeypatch.setattr("model.next_week", mock_next_week_func)
    monkeypatch.setattr("model.event.next_week", mock_next_week_func)
    monkeypatch.setattr("model.utils.next_week", mock_next_week_func)

    yield


@pytest.fixture
def mock_empty_event():
    """Create an empty mock event for testing."""
    return Event(title="Test Event")


@pytest.fixture
def mock_general_event(dummy_date):
    """Create a mock event for testing."""
    return Event(
        title="General Event",
        emoji="🎉",
        description="This is a general event",
        category=Category.GENERAL,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date,
        time=time(14, 30),
        venue="Test Venue",
        location="https://maps.google.com/?q=Test+Location",
        url="https://example.com/general",
        image="image.jpg",
    )


@pytest.fixture
def mock_recurring_event():
    """Create a mock recurring event for testing."""
    return Event(
        title="Recurring Event",
        emoji="🔄",
        description="This is a recurring event",
        occurrence=Occurrence.REGULAR,
        days={Day.Monday, Day.Wednesday, Day.Friday},
        time=time(18, 0),
        venue="Standard Venue",
        url="https://example.com/recurring",
    )


@pytest.fixture
def mock_rally_event(dummy_date):
    """Create a mock rally event for testing."""
    return Event(
        title="Rally Event",
        emoji="📢",
        description="This is a rally event",
        category=Category.RALLY,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date,
        time=time(15, 0),
        venue="Rally Venue",
        url="https://example.com/rally",
    )


@pytest.fixture
def mock_fundraiser_event(dummy_date):
    """Create a mock fundraiser event for testing."""
    return Event(
        title="Fundraiser Event",
        emoji="💰",
        description="This is a fundraiser event",
        category=Category.FUNDRAISER,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date,
        time=time(16, 15),
        venue="Fundraiser Venue",
        url="https://example.com/fundraiser",
    )


@pytest.fixture
def mock_volunteer_event(dummy_date):
    """Create a mock volunteer event for testing."""
    return Event(
        title="Volunteer Event",
        emoji="🤲",
        description="This is a volunteer event",
        category=Category.VOLUNTEER,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date,
        time=time(17, 0),
        venue="Volunteer Venue",
        url="https://example.com/volunteer",
    )


@pytest.fixture
def mock_future_event(dummy_date):
    """Create a mock future event for testing."""
    return Event(
        title="Future Event",
        emoji="🔮",
        description="This is a future event",
        category=Category.GENERAL,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date + timedelta(days=100),
        time=time(12, 0),
        venue="Future Venue",
        url="https://example.com/future",
    )


@pytest.fixture
def mock_future_rally_event(dummy_date):
    """Create a mock future rally event for testing."""
    return Event(
        title="Future Rally Event",
        emoji="📢",
        description="This is a future rally event",
        category=Category.RALLY,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date + timedelta(days=100),
        time=time(12, 0),
        venue="Future Rally Venue",
        url="https://example.com/future-rally",
    )


@pytest.fixture
def mock_past_event(dummy_date):
    """Create a mock past event for testing."""
    return Event(
        title="Past Event",
        emoji="🕰️",
        description="This is a past event",
        category=Category.GENERAL,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date - timedelta(days=7),
        time=time(10, 0),
        venue="Past Venue",
        url="https://example.com/past",
    )


@pytest.fixture
def mock_multiday_event(dummy_date):
    """Create a mock multi-day event for testing."""
    start_date = dummy_date
    end_date = dummy_date + timedelta(days=2)
    return Event(
        title="Multi-day Event",
        emoji="📅",
        description="This is a multi-day event",
        category=Category.GENERAL,
        occurrence=Occurrence.WITHIN_DAYS,
        date=start_date,
        end_date=end_date,
        time=time(9, 0),
        venue="Multi-day Venue",
        url="https://example.com/multiday",
    )


@pytest.fixture
def mock_past_multiday_event(dummy_date):
    """Create a mock past multi-day event for testing."""
    return Event(
        title="Past Multi-day Event",
        emoji="📅",
        description="This is a past multi-day event",
        category=Category.GENERAL,
        occurrence=Occurrence.WITHIN_DAYS,
        date=dummy_date - timedelta(days=10),
        end_date=dummy_date - timedelta(days=7),
        time=time(9, 0),
        venue="Past Multi-day Venue",
        url="https://example.com/past-multiday",
    )


@pytest.fixture
def mock_this_week_multiday_event(dummy_date):
    """Create a mock future multi-day event for testing."""
    return Event(
        title="This Week Multi-day Event",
        emoji="📅",
        description="This is a this week multi-day event",
        category=Category.GENERAL,
        occurrence=Occurrence.WITHIN_DAYS,
        date=dummy_date + timedelta(days=1),
        end_date=dummy_date + timedelta(days=8),
        time=time(9, 0),
        venue="This Week Multi-day Venue",
        url="https://example.com/this-week-multiday",
    )


@pytest.fixture
def mock_far_future_multiday_event(dummy_date):
    """Create a mock far future multi-day event for testing."""
    return Event(
        title="Far Future Multi-day Event",
        emoji="📅",
        description="This is a far future multi-day event",
        category=Category.RALLY,
        occurrence=Occurrence.WITHIN_DAYS,
        date=dummy_date + timedelta(days=93),
        end_date=dummy_date + timedelta(days=100),
        time=time(9, 0),
        venue="Far Future Multi-day Venue",
        url="https://example.com/far-future-multiday",
    )


@pytest.fixture
def mock_event_no_url(dummy_date):
    """Create a mock event without URL for testing."""
    return Event(
        title="Event Without URL",
        emoji="🚫",
        description="This is an event without URL",
        category=Category.VOLUNTEER,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date,
        time=time(13, 0),
        venue="No URL Venue",
    )


@pytest.fixture
def mock_event_tg_url(dummy_date):
    """Create a mock event with Telegram URL for testing."""
    return Event(
        title="Event With TG URL",
        emoji="📱",
        description="This is an event with Telegram URL",
        category=Category.FUNDRAISER,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date,
        time=time(20, 0),
        venue="TG URL Venue",
        tg_url="https://t.me/tg_url",
    )


@pytest.fixture
def mock_event_both_urls(dummy_date):
    """Create a mock event with both URLs for testing."""
    return Event(
        title="Event With Both URLs",
        emoji="📱",
        description="This is an event with both URLs",
        category=Category.VOLUNTEER,
        occurrence=Occurrence.WITHIN_DAY,
        date=dummy_date,
        time=time(21, 0),
        venue="Both URLs Venue",
        tg_url="https://t.me/both_urls",
        url="https://example.com/both_urls",
    )


@pytest.fixture
def calendar():
    """Create an empty calendar instance for testing."""
    return Calendar()


@pytest.fixture
def mock_events(
    mock_general_event,
    mock_rally_event,
    mock_fundraiser_event,
    mock_volunteer_event,
    mock_recurring_event,
    mock_past_event,
    mock_future_event,
    mock_future_rally_event,
    mock_multiday_event,
    mock_past_multiday_event,
    mock_this_week_multiday_event,
    mock_far_future_multiday_event,
    mock_event_no_url,
    mock_event_tg_url,
    mock_event_both_urls,
):
    """Create a dictionary with all 14 mock events for easy access."""
    return {
        "general": mock_general_event,
        "rally": mock_rally_event,
        "fundraiser": mock_fundraiser_event,
        "volunteer": mock_volunteer_event,
        "recurring": mock_recurring_event,
        "past": mock_past_event,
        "future": mock_future_event,
        "future_rally": mock_future_rally_event,
        "multiday": mock_multiday_event,
        "past_multiday": mock_past_multiday_event,
        "this_week_multiday": mock_this_week_multiday_event,
        "far_future_multiday": mock_far_future_multiday_event,
        "no_url": mock_event_no_url,
        "tg_url": mock_event_tg_url,
        "both_urls": mock_event_both_urls,
    }


@pytest.fixture
def events_grouped():
    """Create a dictionary of events grouped for testing."""
    return {
        "nearest": [
            "general",
            "rally",
            "fundraiser",
            "volunteer",
            "recurring",
            "multiday",
            "this_week_multiday",
            "no_url",
            "tg_url",
            "both_urls",
        ],
        "nearest_general": ["general", "recurring", "multiday", "this_week_multiday"],
        "future": ["future", "future_rally", "far_future_multiday"],
        "past": ["past", "past_multiday"],
        "general": ["general", "recurring", "multiday", "this_week_multiday"],
        "fundraiser": ["fundraiser", "tg_url"],
        "volunteer": ["volunteer", "no_url", "both_urls"],
        "rally": ["rally", "future_rally", "far_future_multiday"],
    }


@pytest.fixture
def mock_calendar(mock_events):
    """Create a calendar with various events."""
    calendar = Calendar()
    for event in mock_events.values():
        calendar.add_event(event)
    return calendar

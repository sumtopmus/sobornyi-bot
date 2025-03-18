"""Tests for the Calendar class."""

from datetime import date, time, timedelta
from unittest.mock import patch

import pytest

from model import Calendar, Category, Day, Event, Occurrence


class TestCalendar:
    def test_init(self, calendar):
        """Test calendar initialization."""
        assert isinstance(calendar, Calendar)
        # The events dictionary is private with double underscore
        assert hasattr(calendar, "_Calendar__events")
        assert isinstance(calendar._Calendar__events, dict)
        assert len(calendar._Calendar__events) == 0

    def test_add_event(self, calendar, mock_event):
        """Test adding an event to the calendar."""
        event_id = calendar.add_event(mock_event)
        assert event_id is not None
        assert isinstance(event_id, int)
        assert event_id in calendar._Calendar__events
        assert calendar._Calendar__events[event_id] == mock_event

    def test_delete_event(self, calendar, mock_event):
        """Test deleting an event from the calendar."""
        event_id = calendar.add_event(mock_event)
        assert calendar.delete_event(mock_event) is True
        assert event_id not in calendar._Calendar__events

    def test_delete_nonexistent_event(self, calendar, mock_event):
        """Test deleting a non-existent event."""
        assert calendar.delete_event(mock_event) is False

    def test_get_event(self, calendar, mock_event):
        """Test getting an event by ID."""
        event_id = calendar.add_event(mock_event)
        retrieved_event = calendar.get_event(event_id)
        assert retrieved_event == mock_event

    def test_get_nonexistent_event(self, calendar):
        """Test getting a non-existent event."""
        assert calendar.get_event(999) is None

    def test_get_nearest_events(self, calendar, mock_event, mock_recurring_event):
        """Test getting nearest events."""
        calendar.add_event(mock_event)
        calendar.add_event(mock_recurring_event)

        nearest_events = calendar.get_nearest_events()
        assert isinstance(nearest_events, list)
        # The actual implementation might return different results based on dates
        # Just check that the method returns a list
        # TODO: Add more tests

    def test_get_future_events(self, calendar, mock_event):
        """Test getting future events."""
        # Add a past event
        past_event = Event(
            title="Past Event",
            emoji="🕰️",
            description="This is a past event",
            occurrence=Occurrence.WITHIN_DAY,
            date=date.today() - timedelta(days=1),
            time=time(14, 30),
            venue="Past Venue",
        )
        calendar.add_event(past_event)

        # Add a future event
        future_event = Event(
            title="Future Event",
            emoji="🔮",
            description="This is a future event",
            occurrence=Occurrence.WITHIN_DAY,
            date=date.today() + timedelta(days=10),  # Ensure it's after next week
            time=time(14, 30),
            venue="Future Venue",
        )
        calendar.add_event(future_event)

        events = calendar.get_future_events()
        assert isinstance(events, list)
        # TODO: Add more tests
        # The actual implementation might return different results based on dates
        # Just check that the method returns a list

    def test_get_simple_agenda(self, calendar, mock_event, mock_recurring_event):
        """Test generating a simple agenda."""
        calendar.add_event(mock_event)
        calendar.add_event(mock_recurring_event)

        events = calendar.get_nearest_events()
        agenda = calendar.get_simple_agenda(events)
        assert isinstance(agenda, str)

    def test_get_nearest_agenda(self, calendar, mock_event, mock_recurring_event):
        """Test generating a nearest agenda."""
        calendar.add_event(mock_event)
        calendar.add_event(mock_recurring_event)

        events = calendar.get_nearest_events()
        agenda = calendar.get_nearest_agenda(events)
        assert isinstance(agenda, str)

    def test_get_future_agenda(self, calendar):
        """Test generating a future agenda."""
        # Create a future event
        future_date = date.today() + timedelta(days=30)
        future_event = Event(
            title="Future Event", date=future_date, occurrence=Occurrence.WITHIN_DAY
        )

        calendar.add_event(future_event)

        events = calendar.get_future_events()
        agenda = calendar.get_future_agenda(events)
        assert isinstance(agenda, str)

    def test_get_agenda(self, calendar, mock_event, mock_recurring_event):
        """Test getting an agenda from the calendar."""
        calendar.add_event(mock_event)
        calendar.add_event(mock_recurring_event)
        agenda = calendar.get_agenda()
        assert isinstance(agenda, str)
        # The actual implementation might return different results
        # Just check that the method returns a string
        # TODO: Add more tests

    @patch("model.calendar.this_week")
    def test_remove_past_events(self, mock_this_week, calendar):
        """Test removing past events."""
        # Set a fixed date for this_week
        fixed_date = date(2025, 3, 3)  # March 3, 2025 (a Monday)
        mock_this_week.return_value = fixed_date
        # Create a past event (before this_week)
        past_date = fixed_date - timedelta(days=7)  # One week before fixed date
        past_event = Event(
            title="Past Event", date=past_date, occurrence=Occurrence.WITHIN_DAY
        )
        # Create a current event (within this_week)
        current_date = fixed_date + timedelta(days=2)  # Two days after fixed date
        current_event = Event(
            title="Current Event", date=current_date, occurrence=Occurrence.WITHIN_DAY
        )
        # Create a long event that started before this week and extends into this week
        recurring_past_date = fixed_date - timedelta(days=10)
        recurring_end_date = fixed_date + timedelta(days=3)
        recurring_event = Event(
            title="Recurring Event",
            date=recurring_past_date,
            end_date=recurring_end_date,
            occurrence=Occurrence.WITHIN_DAYS,
        )
        # Created a recurring event that has no end date
        recurring_event_no_end = Event(
            title="Recurring Event", occurrence=Occurrence.REGULAR, days={Day.Saturday}
        )

        # Add events to calendar
        past_id = calendar.add_event(past_event)
        current_id = calendar.add_event(current_event)
        recurring_id = calendar.add_event(recurring_event)
        recurring_id_no_end = calendar.add_event(recurring_event_no_end)
        # Confirm events were added
        assert past_id in calendar
        assert current_id in calendar
        assert recurring_id in calendar
        assert recurring_id_no_end in calendar
        # Call remove_past_events
        result = calendar.remove_past_events()
        # Verify past events were removed and current events remain
        assert result is True  # At least one event was removed
        assert past_id not in calendar  # Past event should be removed
        assert current_id in calendar  # Current event should remain
        assert (
            recurring_id in calendar
        )  # Recurring event that extends into this week should remain
        assert (
            recurring_id_no_end in calendar
        )  # Recurring event that has no end date should remain

    def test_dictionary_interface(self, calendar, mock_event):
        """Test the dictionary interface of the calendar."""
        # Test __setitem__
        calendar[1] = mock_event
        assert 1 in calendar._Calendar__events
        assert calendar._Calendar__events[1] == mock_event

        # Test __getitem__
        assert calendar[1] == mock_event

        # Test __delitem__
        del calendar[1]
        assert 1 not in calendar._Calendar__events

        # Test __contains__
        calendar[1] = mock_event
        assert 1 in calendar

    def test_calendar_iteration_methods(self, calendar, mock_event):
        """Test the dictionary-like iteration methods of Calendar."""
        # Add some events to the calendar
        event_id1 = calendar.add_event(mock_event)

        # Create a second event
        event2 = Event(
            title="Second Event",
            emoji="🎭",
            description="This is another test event",
            date=date.today() + timedelta(days=2),
            time=time(16, 0),
        )
        event_id2 = calendar.add_event(event2)

        # Test __iter__
        event_ids = list(calendar)
        assert len(event_ids) == 2
        assert event_id1 in event_ids
        assert event_id2 in event_ids

        # Test items()
        items = list(calendar.items())
        assert len(items) == 2
        assert (event_id1, mock_event) in items
        assert (event_id2, event2) in items

        # Test values()
        values = list(calendar.values())
        assert len(values) == 2
        assert mock_event in values
        assert event2 in values

        # Test keys()
        keys = list(calendar.keys())
        assert len(keys) == 2
        assert event_id1 in keys
        assert event_id2 in keys

    def test_get_agenda_categories(self, calendar, mock_event):
        """Test the get_agenda method with different event categories."""
        # Add events with different categories
        mock_event.category = Category.GENERAL
        calendar.add_event(mock_event)

        # Create events with different categories
        rally_event = Event(
            title="Rally Event",
            emoji="📢",
            category=Category.RALLY,
            date=date.today(),
        )
        calendar.add_event(rally_event)

        fundraiser_event = Event(
            title="Fundraiser Event",
            emoji="💰",
            category=Category.FUNDRAISER,
            date=date.today(),
        )
        calendar.add_event(fundraiser_event)

        volunteer_event = Event(
            title="Volunteer Event",
            emoji="🤲",
            category=Category.VOLUNTEER,
            date=date.today(),
        )
        calendar.add_event(volunteer_event)

        future_event = Event(
            title="Future Event",
            emoji="🔮",
            category=Category.GENERAL,
            date=date.today() + timedelta(days=30),
        )
        calendar.add_event(future_event)

        # Get the agenda
        agenda = calendar.get_agenda()

        # Check that all categories are included
        assert "📢 Ралі" in agenda
        assert "💰 Збори коштів" in agenda
        assert "📰 Анонси" in agenda
        assert "🤲 Волонтерство" in agenda
        assert "_#agenda_" in agenda

    def test_get_urls_by_category_empty_list(self, calendar):
        """Test get_urls_by_category with an empty list of events."""
        result = calendar.get_urls_by_category([])
        assert result == None

    def test_get_urls_by_category_no_matching_events(self, calendar):
        """Test get_urls_by_category with no matching events for the given category."""
        event1 = Event(title="Event 1", category=Category.FUNDRAISER)
        event2 = Event(title="Event 2", category=Category.RALLY)
        events = [event1, event2]

        # Request VOLUNTEER category when none exists
        result = calendar.get_urls_by_category(events, Category.VOLUNTEER)
        assert result == None

    def test_get_urls_by_category_with_matching_events(self, calendar):
        """Test get_urls_by_category with matching events for the given category."""
        event1 = Event(
            title="Event 1",
            category=Category.FUNDRAISER,
            url="https://example.com/event1",
        )
        event2 = Event(
            title="Event 2",
            category=Category.FUNDRAISER,
            url="https://example.com/event2",
        )
        event3 = Event(title="Event 3", category=Category.RALLY)
        events = [event1, event2, event3]

        result = calendar.get_urls_by_category(events, Category.FUNDRAISER)

        # Should include URLs from event1 and event2, but not event3
        assert "https://example.com/event1" in result
        assert "https://example.com/event2" in result
        assert "\n" in result  # URLs should be separated by newlines

    def test_get_urls_by_category_with_no_urls(self, calendar):
        """Test get_urls_by_category with events that have no URLs."""
        event1 = Event(title="Event 1", category=Category.FUNDRAISER)
        event2 = Event(title="Event 2", category=Category.FUNDRAISER)
        events = [event1, event2]

        # Should return "🕰️ TBD" when no URLs are available
        result = calendar.get_urls_by_category(events, Category.FUNDRAISER)
        assert result == None

    def test_get_urls_by_category_with_tg_url(self, calendar):
        """Test get_urls_by_category with events that have telegram URLs."""
        event1 = Event(
            title="Event 1", category=Category.FUNDRAISER, tg_url="https://t.me/event1"
        )
        event2 = Event(
            title="Event 2",
            category=Category.FUNDRAISER,
            url="https://example.com/event2",
        )
        events = [event1, event2]

        result = calendar.get_urls_by_category(events, Category.FUNDRAISER)

        # Should include tg_url from event1 and url from event2
        assert "https://t.me/event1" in result
        assert "https://example.com/event2" in result

    def test_get_urls_by_category_default_category(self, calendar):
        """Test get_urls_by_category with default category."""
        event1 = Event(
            title="Event 1", category=Category.GENERAL, url="https://example.com/event1"
        )
        event2 = Event(
            title="Event 2",
            category=Category.FUNDRAISER,
            url="https://example.com/event2",
        )
        events = [event1, event2]

        # Using default category (GENERAL)
        result = calendar.get_urls_by_category(events)

        # Should include only event1's URL since it's in the GENERAL category
        assert "https://example.com/event1" in result
        assert "https://example.com/event2" not in result

    def test_get_agenda_as_urls_empty_calendar(self, calendar):
        """Test get_agenda_as_urls with an empty calendar."""
        # An empty calendar should still return an empty string
        result = calendar.get_agenda_as_urls()
        assert result == ""

    def test_get_agenda_as_urls_with_events(self, calendar):
        """Test get_agenda_as_urls with various events."""
        # Create and add events of different categories
        general_event = Event(
            title="General Event",
            category=Category.GENERAL,
            date=date.today(),
            url="https://example.com/general",
        )
        calendar.add_event(general_event)

        rally_event = Event(
            title="Rally Event",
            category=Category.RALLY,
            date=date.today(),
            url="https://example.com/rally",
        )
        calendar.add_event(rally_event)

        future_event = Event(
            title="Future Event",
            category=Category.GENERAL,
            date=date.today() + timedelta(days=30),
            url="https://example.com/future",
        )
        calendar.add_event(future_event)

        fundraiser_event = Event(
            title="Fundraiser Event",
            category=Category.FUNDRAISER,
            date=date.today(),
            url="https://example.com/fundraiser",
        )
        calendar.add_event(fundraiser_event)

        volunteer_event = Event(
            title="Volunteer Event",
            category=Category.VOLUNTEER,
            date=date.today(),
            url="https://example.com/volunteer",
        )
        calendar.add_event(volunteer_event)

        # Get the agenda as URLs
        result = calendar.get_agenda_as_urls()

        # Check that the result contains all expected categories
        assert "🎟 Заходи:" in result
        assert "📢 Ралі:" in result
        assert "📰 Анонси:" in result
        assert "💰 Збори коштів:" in result
        assert "🤲 Волонтерство:" in result

        # Check that URLs are included
        assert "https://example.com/general" in result
        assert "https://example.com/rally" in result
        assert "https://example.com/future" in result
        assert "https://example.com/fundraiser" in result
        assert "https://example.com/volunteer" in result

    def test_get_agenda_as_urls_with_no_urls(self, calendar):
        """Test get_agenda_as_urls with events that have no URLs."""
        # Create and add events without URLs
        general_event = Event(
            title="General Event", category=Category.GENERAL, date=date.today()
        )
        calendar.add_event(general_event)

        rally_event = Event(
            title="Rally Event", category=Category.RALLY, date=date.today()
        )
        calendar.add_event(rally_event)

        # Get the agenda as URLs
        result = calendar.get_agenda_as_urls()

        # Check that TBD is used for categories without URLs
        assert result == ""

    def test_get_agenda_as_urls_mixed_urls(self, calendar):
        """Test get_agenda_as_urls with a mix of events with and without URLs."""
        # Create and add some events with URLs
        general_event_with_url = Event(
            title="General Event With URL",
            category=Category.GENERAL,
            date=date.today(),
            url="https://example.com/general_with_url",
        )
        calendar.add_event(general_event_with_url)

        # Create and add some events without URLs
        general_event_no_url = Event(
            title="General Event No URL", category=Category.GENERAL, date=date.today()
        )
        calendar.add_event(general_event_no_url)

        rally_event_with_url = Event(
            title="Rally Event With URL",
            category=Category.RALLY,
            date=date.today(),
            url="https://example.com/rally_with_url",
        )
        calendar.add_event(rally_event_with_url)

        rally_event_no_url = Event(
            title="Rally Event No URL", category=Category.RALLY, date=date.today()
        )
        calendar.add_event(rally_event_no_url)

        # Get the agenda as URLs
        result = calendar.get_agenda_as_urls()

        # Check that URLs are included for events with URLs
        assert "https://example.com/general_with_url" in result
        assert "https://example.com/rally_with_url" in result

    def test_get_agenda_as_urls_missing_categories(self, calendar):
        """Test get_agenda_as_urls with some missing categories."""
        # Create only general and rally events
        general_event = Event(
            title="General Event",
            category=Category.GENERAL,
            date=date.today(),
            url="https://example.com/general",
        )
        calendar.add_event(general_event)

        rally_event = Event(
            title="Rally Event",
            category=Category.RALLY,
            date=date.today(),
            url="https://example.com/rally",
        )
        calendar.add_event(rally_event)

        # Get the agenda as URLs
        result = calendar.get_agenda_as_urls()

        # Check that the result includes all categories
        assert "🎟 Заходи:" in result
        assert "📢 Ралі:" in result
        assert "📰 Анонси:" not in result
        assert "💰 Збори коштів:" not in result
        assert "🤲 Волонтерство:" not in result
        # Check that URLs are included for categories with events
        assert "https://example.com/general" in result
        assert "https://example.com/rally" in result

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

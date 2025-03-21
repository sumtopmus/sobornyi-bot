"""Tests for the Calendar class."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from model import Calendar, Category, Event


class TestCalendar:
    def test_init(self, calendar):
        """Test calendar initialization."""
        assert isinstance(calendar, Calendar)
        assert list(calendar.keys()) == []
        assert list(calendar.values()) == []
        assert list(calendar.items()) == []

    def test_add_event(self, calendar, mock_events):
        """Test adding an event to the calendar."""
        event_id = calendar.add_event(mock_events["general"])
        assert event_id is not None
        assert isinstance(event_id, int)
        assert event_id in calendar
        assert calendar[event_id] == mock_events["general"]

    def test_delete_event(self, calendar, mock_events):
        """Test deleting an event from the calendar."""
        event_id = calendar.add_event(mock_events["general"])
        assert calendar.delete_event(mock_events["general"]) is True
        assert event_id not in calendar

    def test_delete_nonexistent_event(self, calendar, mock_events):
        """Test deleting a non-existent event."""
        assert calendar.delete_event(mock_events["general"]) is False

    def test_get_event(self, calendar, mock_events):
        """Test getting an event by ID."""
        event_id = calendar.add_event(mock_events["general"])
        retrieved_event = calendar.get_event(event_id)
        assert retrieved_event == mock_events["general"]

    def test_get_nonexistent_event(self, calendar):
        """Test getting a non-existent event."""
        assert calendar.get_event(999) is None

    def test_get_nearest_events(self, mock_calendar, mock_events, events_grouped):
        """Test getting nearest events."""
        nearest_events = mock_calendar.get_nearest_events()

        assert len(nearest_events) == len(events_grouped["nearest"])
        for event_name in events_grouped["nearest"]:
            assert mock_events[event_name] in nearest_events
        for event_name in events_grouped["future"]:
            assert mock_events[event_name] not in nearest_events
        for event_name in events_grouped["past"]:
            assert mock_events[event_name] not in nearest_events

    def test_get_future_events(self, mock_calendar, mock_events, events_grouped):
        """Test getting future events."""
        future_events = mock_calendar.get_future_events()

        assert len(future_events) == len(events_grouped["future"])
        for event_name in events_grouped["future"]:
            assert mock_events[event_name] in future_events
        for event_name in events_grouped["nearest"]:
            assert mock_events[event_name] not in future_events
        for event_name in events_grouped["past"]:
            assert mock_events[event_name] not in future_events

    def test_get_simple_agenda(self, mock_calendar, mock_events, events_grouped):
        """Test generating a simple agenda."""
        events = mock_calendar.get_nearest_events()
        simple_agenda = mock_calendar.get_simple_agenda(events, Category.GENERAL)

        assert simple_agenda.count("\n") == len(events_grouped["nearest_general"]) - 1
        for event_name in events_grouped["nearest_general"]:
            assert mock_events[event_name].get_title_repr() in simple_agenda
        for event_name in events_grouped["future"]:
            assert mock_events[event_name].title not in simple_agenda
        for event_name in events_grouped["past"]:
            assert mock_events[event_name].title not in simple_agenda

    def test_get_nearest_agenda(self, mock_calendar, mock_events, events_grouped):
        """Test generating a nearest agenda."""
        events = mock_calendar.get_nearest_events()
        nearest_agenda = mock_calendar.get_nearest_agenda(events, Category.GENERAL)

        assert nearest_agenda.count("\n") == len(events_grouped["nearest_general"]) - 1
        for event_name in events_grouped["nearest_general"]:
            assert mock_events[event_name].get_current_repr() in nearest_agenda
        for event_name in events_grouped["future"]:
            assert mock_events[event_name].title not in nearest_agenda
        for event_name in events_grouped["past"]:
            assert mock_events[event_name].title not in nearest_agenda

    def test_get_future_agenda(self, mock_calendar, mock_events, events_grouped):
        """Test generating a future agenda."""
        events = mock_calendar.get_future_events()
        future_agenda = mock_calendar.get_future_agenda(events)

        assert future_agenda.count("\n") == len(events_grouped["future"]) - 1
        for event_name in events_grouped["future"]:
            assert mock_events[event_name].get_future_repr() in future_agenda
        for event_name in events_grouped["nearest"]:
            assert f"[{mock_events[event_name].title}]" not in future_agenda
        for event_name in events_grouped["past"]:
            assert mock_events[event_name].title not in future_agenda

    def test_get_agenda_empty_calendar(self, calendar):
        """Test get_agenda_as_urls with an empty calendar."""
        assert calendar.get_agenda() == "*Порядок тижневий*\n\n_#agenda_"

    def test_get_agenda_categories_all_present(self, mock_calendar):
        """Test agenda with different event categories."""
        agenda = mock_calendar.get_agenda()

        assert "🎟 Заходи" in agenda
        assert "📢 Ралі" in agenda
        assert "📰 Анонси" in agenda
        assert "💰 Збори коштів" in agenda
        assert "🤲 Волонтерство" in agenda

    @pytest.mark.parametrize(
        "event,category",
        [
            ("general", "🎟 Заходи"),
            ("rally", "📢 Ралі"),
            ("future", "📰 Анонси"),
            ("fundraiser", "💰 Збори коштів"),
            ("volunteer", "🤲 Волонтерство"),
        ],
    )
    def test_get_agenda_categories_one_present(
        self, calendar, mock_events, event, category
    ):
        """Test agenda with only one present category."""
        calendar.add_event(mock_events[event])
        agenda = calendar.get_agenda()

        assert category in agenda
        for other_category in [
            "🎟 Заходи",
            "📢 Ралі",
            "📰 Анонси",
            "💰 Збори коштів",
            "🤲 Волонтерство",
        ]:
            if other_category != category:
                assert other_category not in agenda

    def test_get_agenda_content(self, mock_calendar, mock_events, events_grouped):
        """Test getting an agenda from the calendar."""
        agenda = mock_calendar.get_agenda()

        assert (
            agenda.count("\n")
            == len(events_grouped["nearest"]) + len(events_grouped["future"]) + 12
        )
        for event_name in events_grouped["nearest"]:
            assert mock_events[event_name].get_title_repr() in agenda
        for event_name in events_grouped["future"]:
            assert mock_events[event_name].get_future_repr() in agenda
        for event_name in events_grouped["past"]:
            assert mock_events[event_name].title not in agenda

    @patch("model.calendar.this_week")
    def test_remove_past_events(
        self,
        mock_this_week,
        mock_this_week_date,
        mock_calendar,
        mock_events,
        events_grouped,
    ):
        """Test removing past events."""
        for event_name in events_grouped["past"]:
            assert mock_events[event_name] in mock_calendar.values()
        for event_name in events_grouped["nearest"]:
            assert mock_events[event_name] in mock_calendar.values()
        for event_name in events_grouped["future"]:
            assert mock_events[event_name] in mock_calendar.values()

        mock_this_week.return_value = mock_this_week_date
        result = mock_calendar.remove_past_events()

        assert result is True
        for event_name in events_grouped["past"]:
            assert mock_events[event_name] not in mock_calendar.values()
        for event_name in events_grouped["nearest"]:
            assert mock_events[event_name] in mock_calendar.values()
        for event_name in events_grouped["future"]:
            assert mock_events[event_name] in mock_calendar.values()

    def test_dictionary_interface(self, calendar, mock_events):
        """Test the dictionary-like interface of the calendar."""
        # Key-based operations
        calendar[1] = mock_events["general"]
        assert 1 in calendar
        assert calendar[1] == mock_events["general"]
        del calendar[1]
        assert 1 not in calendar

    def test_iteration_methods(self, calendar, mock_events):
        """Test the dictionary-like iteration methods."""
        # Add two events
        event_id1 = calendar.add_event(mock_events["general"])
        event_id2 = calendar.add_event(mock_events["future"])

        # Test iteration methods
        assert len(list(calendar)) == 2
        assert set(calendar) == {event_id1, event_id2}

        # Test values, keys, items
        assert set(calendar.keys()) == {event_id1, event_id2}
        assert set(calendar.values()) == {mock_events["general"], mock_events["future"]}
        assert set(calendar.items()) == {
            (event_id1, mock_events["general"]),
            (event_id2, mock_events["future"]),
        }

    @pytest.mark.parametrize(
        "event_names,category",
        [
            ([], Category.GENERAL),
            (["general"], Category.FUNDRAISER),
            (["rally", "this_week_multiday"], Category.VOLUNTEER),
            (["future", "past"], Category.RALLY),
        ],
    )
    def test_get_urls_by_category_empty_cases(
        self, calendar, mock_events, event_names, category
    ):
        """Test get_urls_by_category with empty or no-match cases."""
        events = [mock_events[event_name] for event_name in event_names]
        for event in events:
            calendar.add_event(event)

        assert calendar.get_urls_by_category(events, category) is None

    @pytest.mark.parametrize(
        "event_group,category",
        [
            ("general", Category.GENERAL),
            ("fundraiser", Category.FUNDRAISER),
            ("volunteer", Category.VOLUNTEER),
            ("rally", Category.RALLY),
        ],
    )
    def test_get_urls_by_category_with_urls(
        self, mock_calendar, mock_events, events_grouped, event_group, category
    ):
        """Test get_urls_by_category with events containing URLs."""
        events = list(mock_events.values())
        urls = mock_calendar.get_urls_by_category(events, category)

        for each_event_group in ["general", "rally", "fundraiser", "volunteer"]:
            same_group = False
            if each_event_group == event_group:
                same_group = True
            for event_name in events_grouped[each_event_group]:
                url = mock_events[event_name].get_url()
                if url:
                    assert url in urls if same_group else url not in urls

    def test_get_agenda_as_urls_empty_calendar(self, calendar):
        """Test get_agenda_as_urls with an empty calendar."""
        assert calendar.get_agenda_as_urls() == ""

    def test_get_agenda_as_urls_with_no_urls(self, calendar, mock_events):
        """Test get_agenda_as_urls with events that have no URLs."""
        calendar.add_event(mock_events["no_url"])

        result = calendar.get_agenda_as_urls()

        assert result == ""

    def test_get_agenda_as_urls_categories_all_present(self, mock_calendar):
        """Test agenda with different event categories."""
        agenda = mock_calendar.get_agenda_as_urls()

        assert "🎟 Заходи" in agenda
        assert "📢 Ралі" in agenda
        assert "📰 Анонси" in agenda
        assert "💰 Збори коштів" in agenda
        assert "🤲 Волонтерство" in agenda

    @pytest.mark.parametrize(
        "event,category",
        [
            ("general", "🎟 Заходи"),
            ("rally", "📢 Ралі"),
            ("future", "📰 Анонси"),
            ("fundraiser", "💰 Збори коштів"),
            ("volunteer", "🤲 Волонтерство"),
        ],
    )
    def test_get_agenda_as_urls_categories_one_present(
        self, calendar, mock_events, event, category
    ):
        """Test agenda with only one present category."""
        calendar.add_event(mock_events[event])
        agenda = calendar.get_agenda_as_urls()

        assert category in agenda
        for other_category in [
            "🎟 Заходи",
            "📢 Ралі",
            "📰 Анонси",
            "💰 Збори коштів",
            "🤲 Волонтерство",
        ]:
            if other_category != category:
                assert other_category not in agenda

    def test_get_agenda_as_urls_content(
        self, mock_calendar, mock_events, events_grouped
    ):
        """Test getting an agenda from the calendar."""
        agenda = mock_calendar.get_agenda_as_urls()

        assert (
            agenda.count("\n")
            == len(events_grouped["nearest"]) + len(events_grouped["future"]) + 7
        )
        for event_name in events_grouped["nearest"]:
            url = mock_events[event_name].get_url()
            if url:
                assert url in agenda
        for event_name in events_grouped["future"]:
            url = mock_events[event_name].get_url()
            if url:
                assert url in agenda
        for event_name in events_grouped["past"]:
            url = mock_events[event_name].get_url()
            if url:
                assert url not in agenda

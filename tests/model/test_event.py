"""Tests for the Event class."""

from datetime import timedelta
from unittest.mock import patch

import pytest

from format import weekday_name
from model import Day, Event


class TestEvent:
    def test_init(self, mock_general_event):
        """Test event initialization."""
        assert isinstance(mock_general_event, Event)
        assert mock_general_event.title == "General Event"

    def test_to_dict(self, mock_general_event):
        """Test to_dict method."""
        event_dict = mock_general_event.to_dict()

        assert isinstance(event_dict, dict)
        assert event_dict["title"] == mock_general_event.title

    def test_get_hash(self, mock_general_event):
        """Test the get_hash method."""
        assert mock_general_event.get_hash() == mock_general_event.__hash__()
        assert isinstance(mock_general_event.get_hash(), int)

    @pytest.mark.parametrize(
        "has_image,expected",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_has_poster(self, mock_general_event, has_image, expected):
        """Test has_poster method with and without an image."""
        mock_general_event.image = "test_image.jpg" if has_image else None

        assert mock_general_event.has_poster() is expected

    @pytest.mark.parametrize(
        "event_name,expected",
        [
            ("general", "https://example.com/general"),
            ("tg_url", "https://t.me/tg_url"),
            ("no_url", None),
            ("both_urls", "https://example.com/both_urls"),
        ],
    )
    def test_get_url(self, mock_events, event_name, expected):
        """Test get_url method with different URL configurations."""
        assert mock_events[event_name].get_url() == expected

    def test_post_without_image(self, mock_rally_event):
        """Test post method without an image."""
        post = mock_rally_event.post()

        assert "text" in post
        assert "photo" not in post
        assert "caption" not in post

    def test_post_with_image(self, mock_general_event):
        """Test post method with an image."""
        post = mock_general_event.post()

        assert "text" not in post
        assert "photo" in post
        assert post["photo"] == "image.jpg"
        assert "caption" in post

    def test_get_weekdays_empty_set(self, mock_recurring_event):
        """Test weekdays representation with empty days set."""
        mock_recurring_event.days = set()

        assert mock_recurring_event.get_weekdays() == ""

    def test_get_weekdays_single_day(self, mock_recurring_event):
        """Test basic weekdays representation cases."""
        mock_recurring_event.days = {Day.Thursday}

        assert weekday_name[Day.Thursday.value] in mock_recurring_event.get_weekdays()

    def test_get_weekdays_non_consecutive_days(self, mock_recurring_event):
        """Test weekdays representation with non-consecutive days."""
        mock_recurring_event.days = {Day.Monday, Day.Wednesday, Day.Friday}

        weekdays = mock_recurring_event.get_weekdays()

        assert "," in weekdays
        assert weekday_name[Day.Monday.value] in weekdays
        assert weekday_name[Day.Wednesday.value] in weekdays
        assert weekday_name[Day.Friday.value] in weekdays

    def test_get_weekdays_two_consecutive_days(self, mock_recurring_event):
        """Test weekdays representation with two consecutive days."""
        mock_recurring_event.days = {Day.Monday, Day.Tuesday}

        weekdays = mock_recurring_event.get_weekdays()

        assert "-" in weekdays
        assert weekdays.startswith(weekday_name[Day.Monday.value])
        assert weekdays.endswith(weekday_name[Day.Tuesday.value])

    def test_get_weekdays_three_consecutive_days(self, mock_recurring_event):
        """Test weekdays representation with three consecutive days."""
        mock_recurring_event.days = {Day.Monday, Day.Tuesday, Day.Wednesday}

        weekdays = mock_recurring_event.get_weekdays()

        assert "-" in weekdays
        assert weekdays.startswith(weekday_name[Day.Monday.value])
        assert weekdays.endswith(weekday_name[Day.Wednesday.value])

    def test_get_weekdays_end_of_week(self, mock_recurring_event):
        """Test weekdays representation with end-of-week sequence."""
        mock_recurring_event.days = {Day.Friday, Day.Saturday, Day.Sunday}

        weekdays = mock_recurring_event.get_weekdays()

        assert "-" in weekdays  # Should use range notation
        assert weekdays.startswith(weekday_name[Day.Friday.value])
        assert weekdays.endswith(weekday_name[Day.Sunday.value])

    def test_get_weekdays_multiple_sequences(self, mock_recurring_event):
        """Test weekdays representation with multiple day sequences."""
        mock_recurring_event.days = {Day.Monday, Day.Tuesday, Day.Thursday, Day.Friday}

        weekdays = mock_recurring_event.get_weekdays()

        assert "," in weekdays and "-" in weekdays
        assert weekday_name[Day.Monday.value] in weekdays
        assert weekday_name[Day.Tuesday.value] in weekdays
        assert weekday_name[Day.Thursday.value] in weekdays
        assert weekday_name[Day.Friday.value] in weekdays

    def test_get_weekdays_all_days(self, mock_recurring_event):
        """Test weekdays representation with all days of the week."""
        mock_recurring_event.days = {
            Day.Monday,
            Day.Tuesday,
            Day.Wednesday,
            Day.Thursday,
            Day.Friday,
            Day.Saturday,
            Day.Sunday,
        }

        weekdays = mock_recurring_event.get_weekdays()

        assert "-" not in weekdays
        assert weekdays == weekday_name[127]

    def test_get_weekdays_wrap_around(self, mock_recurring_event):
        """Test weekdays representation with week-wrapping sequence."""
        mock_recurring_event.days = {Day.Sunday, Day.Monday}

        weekdays = mock_recurring_event.get_weekdays()

        assert "," in weekdays
        assert weekday_name[Day.Sunday.value] in weekdays
        assert weekday_name[Day.Monday.value] in weekdays

    @pytest.mark.parametrize(
        "title,emoji,expected",
        [
            ("Test Event", "🎉", "🎉 Test Event"),
            ("Test Event", None, "Test Event"),
            ("", "🎉", None),
            (None, "🎉", None),
            ("Test & Event!", "🎭", "🎭 Test & Event!"),
            ("Test Event", "🎉🎊", "🎉🎊 Test Event"),
        ],
    )
    def test_get_title(self, mock_empty_event, title, emoji, expected):
        """Test get_title with different combinations of title and emoji."""
        mock_empty_event.title = title
        mock_empty_event.emoji = emoji
        assert mock_empty_event.get_title() == expected

    @pytest.mark.parametrize(
        "title,emoji,tg_url,url,expected",
        [
            # Basic cases
            ("Test Event", None, None, None, "Test Event"),
            # URL cases
            (
                "Test Event",
                None,
                "https://t.me/event",
                None,
                "[Test Event](https://t.me/event)",
            ),
            (
                "Test Event",
                None,
                None,
                "https://example.com",
                "[Test Event](https://example.com)",
            ),
            (
                "Test Event",
                None,
                "https://t.me/event",
                "https://example.com",
                "[Test Event](https://t.me/event)",
            ),
            # With brackets
            (
                "Test [Event]",
                None,
                "https://t.me/event",
                "https://example.com",
                "[Test (Event)](https://t.me/event)",
            ),
            (
                "Test] [test] Event",
                None,
                "https://t.me/event",
                "https://example.com",
                "[Test) (test) Event](https://t.me/event)",
            ),
            # With other escape characters
            (
                "*Test* _Event_",
                None,
                "https://t.me/event",
                "https://example.com",
                "[\*Test\* \_Event\_](https://t.me/event)",
            ),
            (
                "Test \\ Event",
                None,
                "https://t.me/event",
                "https://example.com",
                "[Test \\ Event](https://t.me/event)",
            ),
            # With emoji
            (
                "Test Event",
                "🎉",
                None,
                "https://example.com",
                "🎉 [Test Event](https://example.com)",
            ),
            (
                "Test Event",
                "🎉",
                "https://t.me/event",
                None,
                "🎉 [Test Event](https://t.me/event)",
            ),
            # Empty/None title
            ("", "🎉", "https://example.com", None, None),
            (None, "🎉", "https://example.com", None, None),
        ],
    )
    def test_get_title_repr(
        self, mock_empty_event, title, emoji, tg_url, url, expected
    ):
        """Test get_title_repr with different combinations."""
        mock_empty_event.title = title
        mock_empty_event.emoji = emoji
        mock_empty_event.tg_url = tg_url
        mock_empty_event.url = url
        assert mock_empty_event.get_title_repr() == expected

    def test_get_current_repr_regular(self, mock_recurring_event):
        """Test current representation of a regular recurring event."""
        current_repr = mock_recurring_event.get_current_repr()

        assert "🗓️" in current_repr

    def test_get_current_repr_time_without_minutes(self, mock_general_event):
        """Test current representation of an event with time having zero minutes."""
        current_repr = mock_general_event.get_current_repr()

        assert "14" in current_repr
        assert ":00" not in current_repr

    def test_get_current_repr_time_with_minutes(self, mock_fundraiser_event):
        """Test current representation of an event with time having non-zero minutes."""
        current_repr = mock_fundraiser_event.get_current_repr()

        assert "16:15" in current_repr

    def test_get_current_repr_no_title(self, mock_general_event):
        """Test current representation returns None when there's no title."""
        mock_general_event.title = None

        assert mock_general_event.get_current_repr() is None

    def test_get_current_repr_with_title(self, mock_general_event):
        """Test current representation when event has a title."""
        current_repr = mock_general_event.get_current_repr()

        assert current_repr is not None
        assert mock_general_event.get_title_repr() in current_repr

    def test_get_current_repr_no_date_or_time(self, mock_general_event):
        """Test current representation when event has neither date nor time."""
        mock_general_event.date = None
        mock_general_event.time = None

        assert (
            mock_general_event.get_current_repr() == mock_general_event.get_title_repr()
        )

    def test_get_current_repr_only_time(self, mock_general_event):
        """Test current representation when event has only time."""
        mock_general_event.date = None

        current_repr = mock_general_event.get_current_repr()

        assert "🗓️" not in current_repr
        assert ":" in current_repr

    def test_get_current_repr_only_date(self, mock_general_event):
        """Test current representation when event has only date."""
        mock_general_event.time = None

        current_repr = mock_general_event.get_current_repr()

        assert "🗓️" in current_repr
        assert "чт" in current_repr
        assert mock_general_event.get_title_repr() in current_repr

    def test_get_current_repr_past_single_day(self, mock_past_event):
        """Test current representation for a completely past single-day event."""
        assert mock_past_event.get_current_repr() is None

    def test_get_current_repr_past_multi_day(self, mock_past_multiday_event):
        """Test current representation for a completely past multi-day event."""
        assert mock_past_multiday_event.get_current_repr() is None

    def test_get_current_repr_end_date_before_next_week(self, mock_multiday_event):
        """Test current representation of an event ending before next week."""
        assert mock_multiday_event.get_current_repr() is not None
        assert (
            mock_multiday_event.end_date.strftime("%m/%d")
            not in mock_multiday_event.get_current_repr()
        )

    def test_get_current_repr_end_date_after_next_week(self, mock_multiday_event):
        """Test current representation of an event ending after next week."""
        mock_multiday_event.end_date = mock_multiday_event.date + timedelta(weeks=1)

        assert mock_multiday_event.get_current_repr() is not None
        assert (
            mock_multiday_event.end_date.strftime("%m/%d")
            in mock_multiday_event.get_current_repr()
        )

    def test_get_current_repr_date_before_this_week_end_date_before_next_week(
        self, mock_multiday_event, dummy_date
    ):
        """Test current representation of an event starting before this week and ending before next week."""
        mock_multiday_event.date = dummy_date - timedelta(weeks=1)
        mock_multiday_event.end_date = dummy_date

        current_repr = mock_multiday_event.get_current_repr()

        assert current_repr is not None
        assert "🗓️до" in current_repr
        assert weekday_name[6] in current_repr

    def test_get_current_repr_date_before_this_week_end_date_after_next_week(
        self, mock_multiday_event, dummy_date
    ):
        """Test current representation of an event starting before this week and ending after next week."""
        mock_multiday_event.date = dummy_date - timedelta(weeks=1)
        mock_multiday_event.end_date = dummy_date + timedelta(weeks=1)

        current_repr = mock_multiday_event.get_current_repr()

        assert current_repr is not None
        assert "🗓️до" in current_repr
        assert mock_multiday_event.end_date.strftime("%m/%d") in current_repr

    def test_get_current_repr_date_this_week_end_date_before_next_week(
        self, mock_multiday_event, dummy_date
    ):
        """Test current representation of an event starting this week and ending before next week."""
        mock_multiday_event.date = dummy_date
        mock_multiday_event.end_date = dummy_date + timedelta(days=2)

        current_repr = mock_multiday_event.get_current_repr()

        assert current_repr is not None
        assert weekday_name[mock_multiday_event.date.weekday()] in current_repr
        assert (
            f"-{weekday_name[mock_multiday_event.end_date.weekday()]}" in current_repr
        )

    def test_get_current_repr_date_this_week_end_date_after_next_week(
        self, mock_multiday_event, dummy_date
    ):
        """Test current representation of an event starting this week and ending after next week."""
        mock_multiday_event.date = dummy_date
        mock_multiday_event.end_date = dummy_date + timedelta(weeks=1)

        current_repr = mock_multiday_event.get_current_repr()

        assert current_repr is not None
        assert weekday_name[mock_multiday_event.date.weekday()] in current_repr
        assert f"до `{mock_multiday_event.end_date.strftime('%m/%d')}`" in current_repr

    @patch("model.event.clock")
    def test_get_current_repr_emoji_time(self, mock_clock, mock_general_event):
        """Test that clock emoji is included in the time representation."""
        mock_clock.emoji.return_value = "🕒"

        current_repr = mock_general_event.get_current_repr()

        assert current_repr is not None
        assert "🕒" in current_repr
        assert mock_clock.emoji.called

    def test_get_current_repr_regular_no_weekdays(self, mock_recurring_event):
        """Test current representation of a regular event with no weekdays set."""
        mock_recurring_event.days = set()

        current_repr = mock_recurring_event.get_current_repr()

        assert current_repr is not None
        assert "🗓️" in current_repr
        assert mock_recurring_event.get_title_repr() in current_repr

    @patch("model.event.clock")
    def test_get_full_repr_basic(self, mock_clock, mock_general_event):
        """Test that full representation contains required elements."""
        mock_clock.emoji.return_value = "🕒"

        full_repr = mock_general_event.get_full_repr()

        assert mock_general_event.title in full_repr
        assert "_#events_" in full_repr

        assert mock_general_event.emoji in full_repr
        assert mock_general_event.description in full_repr
        assert "🗓️" in full_repr
        assert mock_general_event.date.strftime("%m/%d") in full_repr
        assert "🕒" in full_repr
        assert mock_general_event.time.strftime("%H:%M") in full_repr
        assert "📍" in full_repr
        assert "🔗" in full_repr

    def test_get_full_repr_with_description(self, mock_general_event):
        """Test full representation with a custom description."""
        assert mock_general_event.description in mock_general_event.get_full_repr()

    def test_get_full_repr_with_regular_occurrence(self, mock_recurring_event):
        """Test full representation with regular occurrence and weekdays."""
        full_repr = mock_recurring_event.get_full_repr()

        assert "🗓️" in full_repr
        assert mock_recurring_event.get_weekdays() in full_repr

    def test_get_full_repr_with_no_location_no_venue(self, mock_empty_event):
        """Test full representation with no location and no venue."""
        mock_empty_event.location = None
        mock_empty_event.venue = None
        full_repr = mock_empty_event.get_full_repr()
        assert full_repr is not None
        assert "📍" not in full_repr

    @pytest.mark.parametrize(
        "venue,location,expected_text,expected_present",
        [
            (None, None, None, False),
            ("Test Venue", None, "📍Test Venue", True),
            (None, "https://maps.google.com/?q=Test+Location", "📍[Location]", True),
            (
                "Test Venue",
                "https://maps.google.com/?q=Test+Location",
                "📍[Test Venue]",
                True,
            ),
        ],
    )
    def test_get_full_repr_with_location_venue_combinations(
        self, mock_general_event, venue, location, expected_text, expected_present
    ):
        """Test full representation with different combinations of venue and location."""
        mock_general_event.venue = venue
        mock_general_event.location = location

        full_repr = mock_general_event.get_full_repr()

        assert full_repr is not None
        if expected_present:
            assert expected_text in full_repr
        else:
            assert "📍" not in full_repr

    def test_get_full_repr_with_no_url(self, mock_event_no_url):
        """Test full representation with URL."""
        assert "🔗" not in mock_event_no_url.get_full_repr()

    def test_get_full_repr_with_no_title(self, mock_general_event):
        """Test full representation with no title returns None."""
        mock_general_event.title = None

        assert mock_general_event.get_full_repr() is None

    def test_get_full_repr_with_no_date_or_time(self, mock_general_event):
        """Test full representation with no date or time."""
        mock_general_event.date = None
        mock_general_event.time = None
        mock_general_event.days = set()

        full_repr = mock_general_event.get_full_repr()

        assert full_repr is not None
        assert "🗓️" not in full_repr

    def test_get_full_repr_with_end_date_same_month(
        self, mock_multiday_event, dummy_date
    ):
        """Test full representation with end date in the same month."""
        full_repr = mock_multiday_event.get_full_repr()

        assert mock_multiday_event.date.strftime("%m/%d") in full_repr
        assert mock_multiday_event.end_date.strftime("%d") in full_repr
        assert mock_multiday_event.end_date.strftime("%m/%d") not in full_repr

    def test_get_full_repr_with_end_date_different_month(
        self, mock_multiday_event, dummy_date
    ):
        """Test full representation with end date in a different month."""
        mock_multiday_event.end_date = dummy_date + timedelta(days=31)

        full_repr = mock_multiday_event.get_full_repr()

        assert mock_multiday_event.date.strftime("%m/%d") in full_repr
        assert mock_multiday_event.end_date.strftime("%m/%d") in full_repr

    def test_get_full_repr_end_date_format(self, mock_multiday_event, dummy_date):
        """Test the formatting of end_date in get_full_repr."""
        mock_multiday_event.end_date = dummy_date + timedelta(days=31)

        full_repr = mock_multiday_event.get_full_repr()

        assert f"{mock_multiday_event.date.strftime('%m/%d')}" in full_repr
        assert f"-{mock_multiday_event.end_date.strftime('%m/%d')}" in full_repr

    def test_get_full_repr_end_date_none(self, mock_general_event):
        """Test get_full_repr when end_date is None."""
        full_repr = mock_general_event.get_full_repr()

        assert "-" not in full_repr

    def test_get_future_repr_regular_event(self, mock_recurring_event):
        """Test get_future_repr returns None for regular events."""
        assert mock_recurring_event.get_future_repr() is None

    def test_get_future_repr_non_regular_event(self, mock_future_event):
        """Test get_future_repr for non-regular events."""
        future_repr = mock_future_event.get_future_repr()

        assert mock_future_event.date.strftime("%m/%d") in future_repr

    def test_get_future_repr_with_end_date_same_month(
        self, mock_far_future_multiday_event
    ):
        """Test get_future_repr with end date in the same month."""
        mock_far_future_multiday_event.end_date = (
            mock_far_future_multiday_event.date + timedelta(days=1)
        )

        future_repr = mock_far_future_multiday_event.get_future_repr()

        assert mock_far_future_multiday_event.end_date.strftime("%d") in future_repr

    def test_get_future_repr_with_end_date_different_month(
        self, mock_far_future_multiday_event
    ):
        """Test get_future_repr with end date in a different month."""
        next_month = mock_far_future_multiday_event.date.replace(
            month=mock_far_future_multiday_event.date.month % 12 + 1
        )
        mock_far_future_multiday_event.end_date = next_month

        future_repr = mock_far_future_multiday_event.get_future_repr()

        assert mock_far_future_multiday_event.end_date.strftime("%m/%d") in future_repr

    def test_get_future_repr_with_no_title(self, mock_future_event):
        """Test that get_future_repr returns None for no title."""
        mock_future_event.title = None

        assert mock_future_event.get_future_repr() is None

    def test_copy(self, mock_general_event):
        """Test the copy method."""
        event_copy = mock_general_event.copy()

        # Different object but same attribute values
        assert event_copy is not mock_general_event
        assert event_copy.title == mock_general_event.title
        assert event_copy.emoji == mock_general_event.emoji
        assert event_copy.description == mock_general_event.description
        assert event_copy.occurrence == mock_general_event.occurrence
        assert event_copy.date == mock_general_event.date
        assert event_copy.time == mock_general_event.time
        assert event_copy.venue == mock_general_event.venue
        assert event_copy.location == mock_general_event.location
        assert event_copy.url == mock_general_event.url
        assert event_copy.category == mock_general_event.category

        # Deep copying of collections
        assert event_copy.days is not mock_general_event.days

        # Modifying copy doesn't affect original
        event_copy.title = "Modified Title"
        event_copy.description = "Modified Description"
        assert mock_general_event.title == "General Event"
        assert mock_general_event.description == "This is a general event"

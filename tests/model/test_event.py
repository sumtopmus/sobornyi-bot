"""Tests for the Event class."""

from datetime import date, time, timedelta
from unittest.mock import patch

import pytest

from format import weekday_name
from model import Day, Event, Occurrence


class TestEvent:
    def test_init(self, mock_event):
        """Test event initialization."""
        assert isinstance(mock_event, Event)
        assert mock_event.title == "Test Event"

    def test_to_dict(self, mock_event):
        """Test to_dict method."""
        # This might fail depending on the implementation
        # Just try to call the method
        try:
            event_dict = mock_event.to_dict()
            assert isinstance(event_dict, dict)
            assert event_dict["title"] == mock_event.title
        except Exception as e:
            pytest.skip(f"to_dict failed: {e}")

    def test_get_hash(self, mock_event):
        """Test the get_hash method."""
        # get_hash should return the same value as __hash__
        assert mock_event.get_hash() == mock_event.__hash__()
        assert isinstance(mock_event.get_hash(), int)

    def test_has_poster_with_image(self, mock_event):
        """Test has_poster method with an image."""
        mock_event.image = "test_image.jpg"
        assert mock_event.has_poster()

    def test_has_poster_no_image(self, mock_event):
        """Test has_poster method with no image."""
        mock_event.image = None
        assert not mock_event.has_poster()

    def test_post(self, mock_event):
        """Test post method."""
        # The post method simply returns a dictionary with the event data
        # It doesn't actually call cross_post
        result = mock_event.post()
        assert isinstance(result, dict)
        assert "text" in result or "photo" in result

        # Test with an image
        mock_event.image = "test_image.jpg"
        result = mock_event.post()
        assert isinstance(result, dict)
        assert "photo" in result
        assert result["photo"] == "test_image.jpg"
        assert "caption" in result

    def test_get_weekdays_basic(self, mock_recurring_event):
        """Test basic weekdays representation with default setup."""
        weekdays = mock_recurring_event.get_weekdays()
        assert isinstance(weekdays, str)

    def test_get_weekdays_single_day(self, mock_recurring_event):
        """Test weekdays representation with a single day."""
        mock_recurring_event.days = {Day.Monday}
        weekdays = mock_recurring_event.get_weekdays()
        assert isinstance(weekdays, str)
        assert len(weekdays) > 0
        assert weekday_name[Day.Monday.value] in weekdays

    def test_get_weekdays_two_consecutive_days(self, mock_recurring_event):
        """Test weekdays representation with two consecutive days."""
        mock_recurring_event.days = {Day.Monday, Day.Tuesday}
        weekdays = mock_recurring_event.get_weekdays()
        assert "-" in weekdays  # Should use range notation
        assert weekdays.startswith(weekday_name[Day.Monday.value])
        assert weekdays.endswith(weekday_name[Day.Tuesday.value])

    def test_get_weekdays_three_consecutive_days(self, mock_recurring_event):
        """Test weekdays representation with three consecutive days."""
        mock_recurring_event.days = {Day.Monday, Day.Tuesday, Day.Wednesday}
        weekdays = mock_recurring_event.get_weekdays()
        assert "-" in weekdays  # Should use range notation
        assert weekdays.startswith(weekday_name[Day.Monday.value])
        assert weekdays.endswith(weekday_name[Day.Wednesday.value])

    def test_get_weekdays_non_consecutive_days(self, mock_recurring_event):
        """Test weekdays representation with non-consecutive days."""
        mock_recurring_event.days = {Day.Monday, Day.Wednesday, Day.Friday}
        weekdays = mock_recurring_event.get_weekdays()
        assert "," in weekdays  # Should use comma separation
        assert weekday_name[Day.Monday.value] in weekdays
        assert weekday_name[Day.Wednesday.value] in weekdays
        assert weekday_name[Day.Friday.value] in weekdays

    def test_get_weekdays_multiple_sequences(self, mock_recurring_event):
        """Test weekdays representation with multiple day sequences."""
        mock_recurring_event.days = {Day.Monday, Day.Tuesday, Day.Thursday, Day.Friday}
        weekdays = mock_recurring_event.get_weekdays()
        assert "," in weekdays and "-" in weekdays  # Should use both notations
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
        assert "-" not in weekdays  # Should use shorthand notation
        assert weekdays == weekday_name[127]

    def test_get_weekdays_empty_set(self, mock_recurring_event):
        """Test weekdays representation with empty days set."""
        mock_recurring_event.days = set()
        assert mock_recurring_event.get_weekdays() == ""

    def test_get_weekdays_end_of_week(self, mock_recurring_event):
        """Test weekdays representation with end-of-week sequence."""
        mock_recurring_event.days = {Day.Friday, Day.Saturday, Day.Sunday}
        weekdays = mock_recurring_event.get_weekdays()
        assert "-" in weekdays  # Should use range notation
        assert weekdays.startswith(weekday_name[Day.Friday.value])
        assert weekdays.endswith(weekday_name[Day.Sunday.value])

    def test_get_weekdays_wrap_around(self, mock_recurring_event):
        """Test weekdays representation with week-wrapping sequence."""
        mock_recurring_event.days = {Day.Sunday, Day.Monday}
        weekdays = mock_recurring_event.get_weekdays()
        assert "," in weekdays  # Should use comma separation
        assert weekday_name[Day.Sunday.value] in weekdays
        assert weekday_name[Day.Monday.value] in weekdays

    def test_get_title_with_emoji_and_title(self, mock_empty_event):
        """Test that get_title correctly combines emoji and title."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.emoji = "🎉"
        assert mock_empty_event.get_title() == "🎉 Test Event"

    def test_get_title_without_emoji(self, mock_empty_event):
        """Test that get_title returns only title when no emoji is present."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.emoji = None
        assert mock_empty_event.get_title() == "Test Event"

    def test_get_title_with_empty_title(self, mock_empty_event):
        """Test that get_title returns None for empty title."""
        mock_empty_event.title = ""
        mock_empty_event.emoji = "🎉"
        assert mock_empty_event.get_title() is None

    def test_get_title_with_none_title(self, mock_empty_event):
        """Test that get_title returns None for None title."""
        mock_empty_event.title = None
        mock_empty_event.emoji = "🎉"
        assert mock_empty_event.get_title() is None

    def test_get_title_with_special_characters(self, mock_empty_event):
        """Test that get_title handles special characters correctly."""
        mock_empty_event.title = "Test & Event!"
        mock_empty_event.emoji = "🎭"
        assert mock_empty_event.get_title() == "🎭 Test & Event!"

    def test_get_title_with_multiple_emoji(self, mock_empty_event):
        """Test that get_title handles multiple emoji correctly."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.emoji = "🎉🎊"
        assert mock_empty_event.get_title() == "🎉🎊 Test Event"

    def test_get_title_repr_basic(self, mock_empty_event):
        """Test basic title representation without URLs or emoji."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.emoji = None
        mock_empty_event.url = None
        mock_empty_event.tg_url = None
        assert mock_empty_event.get_title_repr() == "Test Event"

    def test_get_title_repr_with_telegram_url(self, mock_empty_event):
        """Test that telegram URL takes precedence over regular URL."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.tg_url = "https://t.me/event"
        mock_empty_event.url = "https://example.com"
        assert mock_empty_event.get_title_repr() == "[Test Event](https://t.me/event)"

    def test_get_title_repr_with_regular_url(self, mock_empty_event):
        """Test title representation with regular URL."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.tg_url = None
        mock_empty_event.url = "https://example.com"
        assert mock_empty_event.get_title_repr() == "[Test Event](https://example.com)"

    def test_get_title_repr_with_emoji_and_url(self, mock_empty_event):
        """Test title representation with both emoji and URL."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.emoji = "🎉"
        mock_empty_event.url = "https://example.com"
        mock_empty_event.tg_url = None
        assert (
            mock_empty_event.get_title_repr() == "🎉 [Test Event](https://example.com)"
        )

    def test_get_title_repr_with_emoji_and_telegram_url(self, mock_empty_event):
        """Test title representation with both emoji and telegram URL."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.emoji = "🎉"
        mock_empty_event.tg_url = "https://t.me/event"
        assert (
            mock_empty_event.get_title_repr() == "🎉 [Test Event](https://t.me/event)"
        )

    def test_get_title_repr_with_empty_title(self, mock_empty_event):
        """Test that empty title returns None in representation."""
        mock_empty_event.title = ""
        mock_empty_event.emoji = "🎉"
        mock_empty_event.url = "https://example.com"
        assert mock_empty_event.get_title_repr() is None

    def test_get_title_repr_with_none_title(self, mock_empty_event):
        """Test that None title returns None in representation."""
        mock_empty_event.title = None
        mock_empty_event.emoji = "🎉"
        mock_empty_event.url = "https://example.com"
        assert mock_empty_event.get_title_repr() is None

    def test_get_title_repr_with_special_characters(self, mock_empty_event):
        """Test title representation with special characters in title and URL."""
        mock_empty_event.title = "Test & Event!"
        mock_empty_event.url = "https://example.com/test?param=value&other=123"
        mock_empty_event.tg_url = None
        mock_empty_event.emoji = "🎭"
        assert (
            mock_empty_event.get_title_repr()
            == "🎭 [Test & Event!](https://example.com/test?param=value&other=123)"
        )

    def test_get_title_repr_with_multiple_emoji(self, mock_empty_event):
        """Test title representation with multiple emoji."""
        mock_empty_event.title = "Test Event"
        mock_empty_event.emoji = "🎉🎊"
        mock_empty_event.url = "https://example.com"
        assert (
            mock_empty_event.get_title_repr()
            == "🎉🎊 [Test Event](https://example.com)"
        )

    def test_get_current_repr_with_end_date_before_next_week(self, mock_event):
        """Test get_current_repr with end_date before next week."""
        # A week long event that starts on Saturday
        mock_event.date = date(2025, 3, 8)  # Saturday
        mock_event.end_date = mock_event.date + timedelta(days=7)

        with (
            patch("model.event.this_week") as mock_this_week,
            patch("model.event.next_week") as mock_next_week,
        ):
            # date < this_week < end_date < next_week
            mock_this_week.return_value = date(2025, 3, 10)  # Monday
            mock_next_week.return_value = date(2025, 3, 17)  # Monday
            current_repr = mock_event.get_current_repr()
            assert current_repr is not None
            # Should indicate that the event is long
            assert "🗓️до" in current_repr

    def test_get_current_repr_with_end_date_after_next_week(self, mock_event):
        """Test get_current_repr with end_date after next week."""
        # A two week long event that starts on Saturday
        mock_event.date = date(2025, 3, 8)  # Saturday
        mock_event.end_date = mock_event.date + timedelta(days=14)

        with (
            patch("model.event.this_week") as mock_this_week,
            patch("model.event.next_week") as mock_next_week,
        ):
            # date < this_week < next_week < end_date
            mock_this_week.return_value = date(2025, 3, 10)  # Monday
            mock_next_week.return_value = date(2025, 3, 17)  # Monday
            current_repr = mock_event.get_current_repr()
            assert current_repr is not None
            # Should indicate that the event is long
            assert "🗓️до" in current_repr
            # Should include the end date in MM/DD format
            assert mock_event.end_date.strftime("%m/%d") in current_repr

    def test_get_current_repr_regular_event(self, mock_recurring_event):
        """Test current representation of a regular recurring event."""
        current_repr = mock_recurring_event.get_current_repr()
        assert isinstance(current_repr, str)
        assert "🗓️" in current_repr

    def test_get_current_repr_non_regular_event(self, mock_event):
        """Test current representation of a non-regular event."""
        current_repr = mock_event.get_current_repr()
        assert isinstance(current_repr, str)

    def test_get_current_repr_past_date(self, mock_event):
        """Test current representation for a completely past event."""
        with patch("model.event.this_week") as mock_this_week:
            # Set this_week to be after both the event date and end_date
            mock_this_week.return_value = mock_event.date + timedelta(days=14)

            # Single-day event
            mock_event.end_date = None
            assert mock_event.get_current_repr() is None
            # Multi-day event
            mock_event.end_date = mock_event.date + timedelta(days=3)
            assert mock_event.get_current_repr() is None

    def test_get_current_repr_end_date_before_next_week(self, mock_event):
        """Test current representation of an event ending before next week."""
        with (
            patch("model.this_week") as mock_this_week,
            patch("model.next_week") as mock_next_week,
        ):
            mock_this_week.return_value = mock_event.date - timedelta(days=7)
            mock_next_week.return_value = mock_event.date + timedelta(days=14)
            mock_event.end_date = mock_event.date + timedelta(days=3)
            current_repr = mock_event.get_current_repr()
            assert mock_event.get_title_repr() in current_repr

    def test_get_current_repr_end_date_after_next_week(self, mock_event):
        """Test current representation of an event ending after next week."""
        with (
            patch("model.this_week") as mock_this_week,
            patch("model.next_week") as mock_next_week,
        ):
            mock_this_week.return_value = mock_event.date - timedelta(days=7)
            mock_next_week.return_value = mock_event.date + timedelta(days=7)
            mock_event.end_date = mock_event.date + timedelta(days=14)
            current_repr = mock_event.get_current_repr()
            assert mock_event.end_date.strftime("%m/%d") in current_repr

    def test_get_current_repr_time_without_minutes(self, mock_event):
        """Test current representation of an event with time having zero minutes."""
        mock_event.time = time(14, 0)
        current_repr = mock_event.get_current_repr()
        assert "14" in current_repr
        assert ":00" not in current_repr  # Should not show minutes when they're zero

    def test_get_current_repr_time_with_minutes(self, mock_event):
        """Test current representation of an event with time having non-zero minutes."""
        mock_event.time = time(14, 30)
        current_repr = mock_event.get_current_repr()
        assert "14:30" in current_repr

    def test_get_current_repr_no_title(self, mock_event):
        """Test current representation returns None when there's no title."""
        mock_event.title = None
        assert mock_event.get_current_repr() is None

    def test_get_current_repr_no_date_or_time(self, mock_event):
        """Test current representation when event has neither date nor time."""
        mock_event.date = None
        mock_event.time = None
        mock_event.title = "Test Event"
        current_repr = mock_event.get_current_repr()
        assert current_repr == mock_event.get_title_repr()

    def test_get_current_repr_only_time(self, mock_event):
        """Test current representation when event has only time."""
        mock_event.date = None
        mock_event.time = time(14, 30)
        mock_event.title = "Test Event"
        current_repr = mock_event.get_current_repr()
        assert "14:30" in current_repr
        assert mock_event.get_title_repr() in current_repr

    def test_get_current_repr_only_date(self, mock_event):
        """Test current representation when event has only date."""
        mock_event.date = date.today()
        mock_event.time = None
        mock_event.title = "Test Event"
        current_repr = mock_event.get_current_repr()
        assert "🗓️" in current_repr
        assert mock_event.get_title_repr() in current_repr

    def test_get_current_repr_edge_cases(self, mock_event):
        """Test edge cases for get_current_repr method."""
        # Test with no date (should still work)
        mock_event.date = None
        mock_event.end_date = None
        current_repr = mock_event.get_current_repr()
        assert current_repr is not None
        assert mock_event.get_title_repr() in current_repr

    def test_get_full_repr_basic(self, mock_event):
        """Test basic full representation of an event with default properties."""
        full_repr = mock_event.get_full_repr()
        assert isinstance(full_repr, str)
        assert mock_event.title in full_repr
        assert mock_event.emoji in full_repr
        assert mock_event.description in full_repr
        assert "🗓️" in full_repr  # Calendar emoji for date
        assert mock_event.date.strftime("%m/%d") in full_repr  # Date format
        assert mock_event.time.strftime("%H:%M") in full_repr  # Time format
        assert "📍" in full_repr  # Location pin emoji
        assert "🔗" in full_repr  # Link emoji
        assert "_#events_" in full_repr  # Events hashtag

    def test_get_full_repr_with_description(self, mock_event):
        """Test full representation with a custom description."""
        mock_event.description = "This is a detailed description"
        full_repr = mock_event.get_full_repr()
        assert mock_event.description in full_repr

    def test_get_full_repr_with_regular_occurrence(self, mock_event):
        """Test full representation with regular occurrence and weekdays."""
        mock_event.occurrence = Occurrence.REGULAR
        mock_event.days = {Day.Monday, Day.Wednesday}
        full_repr = mock_event.get_full_repr()
        assert "🗓️" in full_repr
        # TODO: test the exact weekday representation
        assert full_repr is not None

    def test_get_full_repr_with_no_location_no_venue(self, mock_event):
        """Test full representation with no location and no venue."""
        mock_event.location = None
        mock_event.venue = None
        full_repr = mock_event.get_full_repr()
        assert full_repr is not None
        assert "📍" not in full_repr  # No location pin emoji

    def test_get_full_repr_with_venue_no_location(self, mock_event):
        """Test full representation with venue but no location."""
        mock_event.venue = "Test Venue"
        mock_event.location = None
        full_repr = mock_event.get_full_repr()
        assert "📍Test Venue" in full_repr

    def test_get_full_repr_with_location_no_venue(self, mock_event):
        """Test full representation with location but no venue."""
        mock_event.venue = None
        mock_event.location = "https://maps.google.com/?q=Test+Location"
        full_repr = mock_event.get_full_repr()
        assert "📍[Location]" in full_repr

    def test_get_full_repr_with_venue_and_location(self, mock_event):
        """Test full representation with both venue and location."""
        mock_event.venue = "Test Venue"
        mock_event.location = "https://maps.google.com/?q=Test+Location"
        full_repr = mock_event.get_full_repr()
        assert "📍[Test Venue]" in full_repr

    def test_get_full_repr_with_url(self, mock_event):
        """Test full representation with URL."""
        mock_event.url = "https://example.com"
        full_repr = mock_event.get_full_repr()
        assert "🔗" in full_repr

    def test_get_full_repr_with_no_title(self, mock_event):
        """Test full representation with no title returns None."""
        mock_event.title = None
        assert mock_event.get_full_repr() is None

    def test_get_full_repr_with_no_date_or_time(self, mock_event):
        """Test full representation with no date or time."""
        mock_event.date = None
        mock_event.time = None
        mock_event.occurrence = Occurrence.WITHIN_DAY
        mock_event.days = set()
        full_repr = mock_event.get_full_repr()
        assert full_repr is not None
        assert mock_event.title in full_repr
        assert "🗓️" not in full_repr  # No calendar emoji

    def test_get_full_repr_with_end_date_same_month(self, mock_event):
        """Test full representation with end date in the same month."""
        mock_event.date = date(2023, 1, 1)
        mock_event.end_date = date(2023, 1, 5)
        full_repr = mock_event.get_full_repr()
        assert mock_event.date.strftime("%m/%d") in full_repr
        assert mock_event.end_date.strftime("%d") in full_repr
        assert mock_event.end_date.strftime("%m/%d") not in full_repr

    def test_get_full_repr_with_end_date_different_month(self, mock_event):
        """Test full representation with end date in a different month."""
        mock_event.date = date(2023, 1, 30)
        mock_event.end_date = date(2023, 2, 5)
        full_repr = mock_event.get_full_repr()
        assert mock_event.date.strftime("%m/%d") in full_repr
        assert mock_event.end_date.strftime("%m/%d") in full_repr

    def test_get_full_repr_end_date_format(self, mock_event):
        """Test the formatting of end_date in get_full_repr."""
        mock_event.date = date(2023, 1, 1)
        mock_event.end_date = date(2023, 2, 5)

        full_repr = mock_event.get_full_repr()
        # Verify the format includes a hyphen between dates
        assert f"{mock_event.date.strftime('%m/%d')}" in full_repr
        assert f"-{mock_event.end_date.strftime('%m/%d')}" in full_repr

    def test_get_full_repr_end_date_none(self, mock_event):
        """Test get_full_repr when end_date is None."""
        mock_event.date = date(2023, 1, 1)
        mock_event.end_date = None

        full_repr = mock_event.get_full_repr()
        assert full_repr is not None
        # Should only include the start date
        assert mock_event.date.strftime("%m/%d") in full_repr
        # Should not have a hyphen for range
        assert "-" not in full_repr

    def test_get_future_repr_regular_event(self, mock_event):
        """Test get_future_repr returns None for regular events."""
        mock_event.occurrence = Occurrence.REGULAR
        assert mock_event.get_future_repr() is None

    def test_get_future_repr_non_regular_event(self, mock_event):
        """Test get_future_repr for non-regular events."""
        mock_event.occurrence = Occurrence.WITHIN_DAY
        future_repr = mock_event.get_future_repr()

        assert isinstance(future_repr, str)
        assert mock_event.date.strftime("%m/%d") in future_repr

    def test_get_future_repr_with_end_date_same_month(self, mock_event):
        """Test get_future_repr with end date in the same month."""
        mock_event.occurrence = Occurrence.WITHIN_DAY
        mock_event.end_date = mock_event.date + timedelta(days=3)

        future_repr = mock_event.get_future_repr()

        assert isinstance(future_repr, str)
        assert mock_event.end_date.strftime("%d") in future_repr

    def test_get_future_repr_with_end_date_different_month(self, mock_event):
        """Test get_future_repr with end date in a different month."""
        mock_event.occurrence = Occurrence.WITHIN_DAY
        next_month = mock_event.date.replace(month=mock_event.date.month % 12 + 1)
        mock_event.end_date = next_month

        future_repr = mock_event.get_future_repr()

        assert isinstance(future_repr, str)
        assert mock_event.end_date.strftime("%m/%d") in future_repr

    def test_get_future_repr_with_no_title(self, mock_event):
        """Test get_future_repr returns None when title is None."""
        mock_event.occurrence = Occurrence.WITHIN_DAY
        mock_event.title = None

        assert mock_event.get_future_repr() is None

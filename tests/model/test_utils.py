"""Tests for the utils."""

from datetime import date

from model import next_week, this_week


def test_get_this_week():
    """Test getting this week's date."""
    this_monday = this_week()
    assert isinstance(this_monday, date)
    # Check that this_monday is a Monday
    assert this_monday.weekday() == 0
    # Check that this_monday is in the current week
    assert (date.today() - this_monday).days <= 6


def test_get_next_week():
    """Test getting next week's date."""
    next_monday = next_week()
    assert isinstance(next_monday, date)
    # Check that next_monday is a Monday
    assert next_monday.weekday() == 0
    # Check that next_monday is in the next week
    assert (next_monday - date.today()).days <= 7

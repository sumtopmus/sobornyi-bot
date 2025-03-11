"""Tests for the menu module."""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update

from handlers.calendar.menu import (
    update_menu,
    calendar_menu,
    events_menu,
    event_menu,
    datetime_menu,
    construct_back_button,
    State,
)
from model.calendar import Day, Occurrence


# Mock the PythonCalendar.get_this_week method at the module level
@pytest.fixture(autouse=True)
def mock_python_calendar():
    with patch("handlers.calendar.menu.PythonCalendar") as mock_calendar:
        mock_calendar.get_this_week.return_value = date(2023, 1, 1)
        yield mock_calendar


class TestMenu:
    """Tests for the menu module."""

    @pytest.mark.asyncio
    async def test_update_menu_with_callback_query(self):
        """Test the update_menu function with a callback query."""
        # Setup
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()
        menu = {"text": "Test menu", "reply_markup": MagicMock()}

        # Call the function
        await update_menu(update, menu)

        # Assertions
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once_with(**menu)
        update.effective_user.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_menu_without_callback_query(self):
        """Test the update_menu function without a callback query."""
        # Setup
        update = MagicMock(spec=Update)
        update.callback_query = None
        update.effective_user = AsyncMock()
        menu = {"text": "Test menu", "reply_markup": MagicMock()}

        # Call the function
        await update_menu(update, menu)

        # Assertions
        update.effective_user.send_message.assert_called_once_with(**menu)

    @pytest.mark.asyncio
    async def test_update_menu_with_new_message(self):
        """Test the update_menu function with new_message=True."""
        # Setup
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()
        menu = {"text": "Test menu", "reply_markup": MagicMock()}

        # Call the function
        await update_menu(update, menu, new_message=True)

        # Assertions
        update.callback_query.answer.assert_not_called()
        update.callback_query.edit_message_text.assert_not_called()
        update.effective_user.send_message.assert_called_once_with(**menu)

    @pytest.mark.asyncio
    async def test_calendar_menu(self, mock_update, mock_context):
        """Test the calendar_menu function."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        context.bot_data = {
            "agenda": {"image": None},
            "calendar": MagicMock(),
        }
        context.user_data = {}

        # Mock the sync_agenda function
        with patch("handlers.calendar.menu.sync_agenda", new=AsyncMock()) as mock_sync:
            # Call the function
            result = await calendar_menu(update, context)

            # Assertions
            assert result == State.CALENDAR_MENU
            mock_sync.assert_called_once_with(context)
            update.callback_query.answer.assert_called_once()
            update.callback_query.edit_message_text.assert_called_once()

            # Check that the keyboard has the expected buttons
            call_args = update.callback_query.edit_message_text.call_args
            assert call_args is not None
            kwargs = call_args[1]
            assert "reply_markup" in kwargs
            keyboard = kwargs["reply_markup"].inline_keyboard

            # Check for Add button
            assert any(
                button.text == "➕ Add"
                and button.callback_data == State.EVENT_ADDING.name
                for row in keyboard
                for button in row
            )

            # Check for Edit button
            assert any(
                button.text == "📝 Edit"
                and button.callback_data == State.EVENT_EDITING.name
                for row in keyboard
                for button in row
            )

            # Check for Poster button (with 🚫 since image is None)
            assert any(
                button.text == "🖼️ Poster 🚫"
                and button.callback_data == State.AGENDA_EDITING_IMAGE.name
                for row in keyboard
                for button in row
            )

            # Check for Preview button
            assert any(
                button.text == "👓 Preview"
                and button.callback_data == State.AGENDA_PREVIEW.name
                for row in keyboard
                for button in row
            )

            # Check for Update button
            assert any(
                button.text == "🔄 Update"
                and button.callback_data == State.CALENDAR_CLEANUP.name
                for row in keyboard
                for button in row
            )

            # Check for Exit button
            assert any(
                button.text == "« Exit" and button.callback_data == State.EXIT.name
                for row in keyboard
                for button in row
            )

            # Check that current_event is set to None
            assert context.user_data.get("current_event") is None
            assert context.user_data.get("state") == State.CALENDAR_MENU

    @pytest.mark.asyncio
    async def test_calendar_menu_with_image(self, mock_update, mock_context):
        """Test the calendar_menu function with an image."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        context.bot_data = {
            "agenda": {"image": "image_data"},
            "calendar": MagicMock(),
        }
        context.user_data = {}

        # Mock the sync_agenda function
        with patch("handlers.calendar.menu.sync_agenda", new=AsyncMock()):
            # Call the function
            await calendar_menu(update, context)

            # Check for Poster button (with ✅ since image exists)
            call_args = update.callback_query.edit_message_text.call_args
            assert call_args is not None
            kwargs = call_args[1]
            keyboard = kwargs["reply_markup"].inline_keyboard

            assert any(
                button.text == "🖼️ Poster ✅"
                and button.callback_data == State.AGENDA_EDITING_IMAGE.name
                for row in keyboard
                for button in row
            )

    @pytest.mark.asyncio
    async def test_calendar_menu_with_prefix_text(self, mock_update, mock_context):
        """Test the calendar_menu function with prefix text."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        context.bot_data = {
            "agenda": {"image": None},
            "calendar": MagicMock(),
        }
        context.user_data = {}

        prefix_text = "This is a prefix text"

        # Mock the sync_agenda function
        with patch("handlers.calendar.menu.sync_agenda", new=AsyncMock()):
            # Call the function
            await calendar_menu(update, context, prefix_text=prefix_text)

            # Check that the text includes the prefix
            call_args = update.callback_query.edit_message_text.call_args
            assert call_args is not None
            kwargs = call_args[1]
            assert prefix_text in kwargs["text"]

    @pytest.mark.asyncio
    async def test_calendar_menu_with_new_message(self, mock_update, mock_context):
        """Test the calendar_menu function with new_message=True."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        context.bot_data = {
            "agenda": {"image": None},
            "calendar": MagicMock(),
        }
        context.user_data = {}

        # Mock the sync_agenda function
        with patch("handlers.calendar.menu.sync_agenda", new=AsyncMock()):
            # Call the function
            await calendar_menu(update, context, new_message=True)

            # Check that send_message was called instead of edit_message_text
            update.callback_query.edit_message_text.assert_not_called()
            update.effective_user.send_message.assert_called_once()

    def test_events_menu_with_events(self, mock_python_calendar):
        """Test the events_menu function with events."""
        # Setup
        from datetime import date

        this_week = date(2023, 1, 1)

        # Create mock events
        event1 = MagicMock()
        event1.date = this_week
        event1.end_date = None
        event1.get_title.return_value = "Event 1"

        event2 = MagicMock()
        event2.date = date(2023, 1, 8)  # Next week
        event2.end_date = None
        event2.get_title.return_value = "Event 2"

        event3 = MagicMock()
        event3.date = None  # Regular event
        event3.end_date = None
        event3.get_title.return_value = "Regular Event"

        events = [
            (1, event1),
            (2, event2),
            (3, event3),
        ]

        # Call the function
        result = events_menu(events)

        # Assertions
        assert "text" in result
        assert "reply_markup" in result

        # Check that the keyboard has the expected buttons
        keyboard = result["reply_markup"].inline_keyboard

        # Check for event buttons
        assert any(
            button.text == "Regular Event"
            and button.callback_data == f"{State.EVENT.name}:3"
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Event 1" and button.callback_data == f"{State.EVENT.name}:1"
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Event 2" and button.callback_data == f"{State.EVENT.name}:2"
            for row in keyboard
            for button in row
        )

        # Check for Search button
        assert any(
            button.text == "🔍 Search"
            and button.callback_data == State.EVENT_FINDING.name
            for row in keyboard
            for button in row
        )

        # Check for Back button
        assert any(
            button.text == "🔙" and button.callback_data == State.CALENDAR_MENU.name
            for row in keyboard
            for button in row
        )

    def test_events_menu_without_events(self, mock_python_calendar):
        """Test the events_menu function without events."""
        # Setup
        events = []

        # Call the function
        result = events_menu(events)

        # Assertions
        assert "text" in result
        assert "reply_markup" in result
        assert "Жодних подій не знайдено." in result["text"]

        # Check that the keyboard has only the back button
        keyboard = result["reply_markup"].inline_keyboard
        assert len(keyboard) == 1
        assert len(keyboard[0]) == 1
        assert keyboard[0][0].text == "🔙"
        assert keyboard[0][0].callback_data == State.CALENDAR_MENU.name

    def test_events_menu_without_search_button(self, mock_python_calendar):
        """Test the events_menu function without the search button."""
        # Setup
        from datetime import date

        this_week = date(2023, 1, 1)

        # Create mock events
        event1 = MagicMock()
        event1.date = this_week
        event1.end_date = None
        event1.get_title.return_value = "Event 1"

        events = [(1, event1)]

        # Call the function
        result = events_menu(events, add_search_button=False)

        # Check that the search button is not present
        keyboard = result["reply_markup"].inline_keyboard
        assert not any(button.text == "🔍 Search" for row in keyboard for button in row)

        # Check that the back button is still present
        assert any(
            button.text == "🔙" and button.callback_data == State.CALENDAR_MENU.name
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_event_menu(self, mock_update, mock_context):
        """Test the event_menu function."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        # Create a mock event with all fields set
        event = MagicMock()
        event.emoji = "🎉"
        event.title = "Test Event"
        event.description = "Test Description"
        event.category = "Test Category"
        event.occurrence = Occurrence.REGULAR
        event.time = "10:00"
        event.date = "2023-01-01"
        event.days = {Day.Monday}
        event.venue = "Test Venue"
        event.location = "Test Location"
        event.url = "https://example.com"
        event.image = "image_data"
        event.get_full_repr.return_value = "Event full representation"

        context.user_data = {
            "current_event": event,
        }

        # Call the function
        result = await event_menu(update, context)

        # Assertions
        assert result == State.EVENT_MENU
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

        # Check that the keyboard has the expected buttons
        call_args = update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert "reply_markup" in kwargs
        keyboard = kwargs["reply_markup"].inline_keyboard

        # Check for field buttons with ✅ since all fields are set
        assert any(
            button.text == "Емоджи ✅"
            and button.callback_data == State.EVENT_EDITING_EMOJI.name
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Назва ✅"
            and button.callback_data == State.EVENT_EDITING_TITLE.name
            for row in keyboard
            for button in row
        )

        # Check for action buttons
        assert any(
            button.text == "👓 Preview"
            and button.callback_data == State.EVENT_PREVIEW.name
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "📺 Publish"
            and button.callback_data == State.EVENT_PUBLISHING.name
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "❌ Delete"
            and button.callback_data == State.EVENT_DELETING.name
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "🔙" and button.callback_data == State.CALENDAR_MENU.name
            for row in keyboard
            for button in row
        )

        # Check that state is set correctly
        assert context.user_data["state"] == State.EVENT_MENU

    @pytest.mark.asyncio
    async def test_event_menu_with_empty_fields(self, mock_update, mock_context):
        """Test the event_menu function with empty fields."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        # Create a mock event with empty fields
        event = MagicMock()
        event.emoji = None
        event.title = "Test Event"  # Title is required
        event.description = None
        event.category = None
        event.occurrence = Occurrence.REGULAR
        event.time = None
        event.date = None
        event.days = set()
        event.venue = None
        event.location = None
        event.url = None
        event.image = None
        event.get_full_repr.return_value = "Event full representation"

        context.user_data = {
            "current_event": event,
        }

        # Call the function
        await event_menu(update, context)

        # Check that the keyboard has buttons with 🚫 for empty fields
        call_args = update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        keyboard = kwargs["reply_markup"].inline_keyboard

        assert any(
            button.text == "Емоджи 🚫"
            and button.callback_data == State.EVENT_EDITING_EMOJI.name
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Опис 🚫"
            and button.callback_data == State.EVENT_EDITING_DESCRIPTION.name
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_event_menu_with_prefix_text(self, mock_update, mock_context):
        """Test the event_menu function with prefix text."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        event = MagicMock()
        event.emoji = "🎉"
        event.title = "Test Event"
        event.description = "Test Description"
        event.category = "Test Category"
        event.occurrence = Occurrence.REGULAR
        event.time = "10:00"
        event.date = None
        event.days = {Day.Monday}
        event.venue = "Test Venue"
        event.location = "Test Location"
        event.url = "https://example.com"
        event.image = "image_data"
        event.get_full_repr.return_value = "Event full representation"

        context.user_data = {
            "current_event": event,
        }

        prefix_text = "This is a prefix text"

        # Call the function
        await event_menu(update, context, prefix_text=prefix_text)

        # Check that the text includes the prefix
        call_args = update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert prefix_text in kwargs["text"]
        assert "Event full representation" in kwargs["text"]

    @pytest.mark.asyncio
    async def test_event_menu_with_new_message_and_prefix(
        self, mock_update, mock_context
    ):
        """Test the event_menu function with new_message=True and prefix text."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        event = MagicMock()
        event.get_full_repr.return_value = "Event full representation"

        context.user_data = {
            "current_event": event,
        }

        prefix_text = "This is a prefix text"

        # Call the function
        await event_menu(update, context, prefix_text=prefix_text, new_message=True)

        # Check that the text is just the prefix (not including the event representation)
        call_args = update.effective_user.send_message.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert kwargs["text"] == prefix_text
        assert "Event full representation" not in kwargs["text"]

    @pytest.mark.asyncio
    async def test_datetime_menu_regular_event(self, mock_update, mock_context):
        """Test the datetime_menu function with a regular event."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        # Create a mock regular event
        event = MagicMock()
        event.occurrence = Occurrence.REGULAR
        event.time = "10:00"
        event.end_time = None
        event.days = {Day.Monday, Day.Wednesday}
        event.get_full_repr.return_value = "Event full representation"

        context.user_data = {
            "current_event": event,
        }

        # Call the function
        result = await datetime_menu(update, context)

        # Assertions
        assert result == State.DATETIME_MENU
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

        # Check that the keyboard has the expected buttons for a regular event
        call_args = update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert "reply_markup" in kwargs
        keyboard = kwargs["reply_markup"].inline_keyboard

        # Check for weekday buttons
        assert any(
            button.text == "Пн ✅"
            and button.callback_data.startswith(f"{State.WEEKDAY.name}:")
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Ср ✅"
            and button.callback_data.startswith(f"{State.WEEKDAY.name}:")
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Вт 🚫"
            and button.callback_data.startswith(f"{State.WEEKDAY.name}:")
            for row in keyboard
            for button in row
        )

        # Check for time buttons
        assert any(
            button.text == "Час (початок) ✅"
            and button.callback_data == State.EVENT_EDITING_TIME.name
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Час (кінець) 🚫"
            and button.callback_data == State.EVENT_EDITING_END_TIME.name
            for row in keyboard
            for button in row
        )

        # Check for back button
        assert any(
            button.text == "🔙" and button.callback_data == State.EVENT_MENU.name
            for row in keyboard
            for button in row
        )

        # Check that state is set correctly
        assert context.user_data["state"] == State.DATETIME_MENU

    @pytest.mark.asyncio
    async def test_datetime_menu_one_time_event(self, mock_update, mock_context):
        """Test the datetime_menu function with a one-time event."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        # Create a mock one-time event
        event = MagicMock()
        event.occurrence = Occurrence.WITHIN_DAY
        event.time = "10:00"
        event.end_time = "12:00"
        event.date = "2023-01-01"
        event.end_date = None
        event.get_full_repr.return_value = "Event full representation"

        context.user_data = {
            "current_event": event,
        }

        # Call the function
        await datetime_menu(update, context)

        # Check that the keyboard has the expected buttons for a one-time event
        call_args = update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        keyboard = kwargs["reply_markup"].inline_keyboard

        # Check for date buttons instead of weekday buttons
        assert any(
            button.text == "Дата (початок) ✅"
            and button.callback_data == State.EVENT_EDITING_DATE.name
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Дата (кінець) 🚫"
            and button.callback_data == State.EVENT_EDITING_END_DATE.name
            for row in keyboard
            for button in row
        )

        # Check for time buttons
        assert any(
            button.text == "Час (початок) ✅"
            and button.callback_data == State.EVENT_EDITING_TIME.name
            for row in keyboard
            for button in row
        )

        assert any(
            button.text == "Час (кінець) ✅"
            and button.callback_data == State.EVENT_EDITING_END_TIME.name
            for row in keyboard
            for button in row
        )

    @pytest.mark.asyncio
    async def test_datetime_menu_with_prefix_text(self, mock_update, mock_context):
        """Test the datetime_menu function with prefix text."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        event = MagicMock()
        event.occurrence = Occurrence.WITHIN_DAY
        event.time = "10:00"
        event.end_time = None
        event.date = "2023-01-01"
        event.end_date = None
        event.get_full_repr.return_value = "Event full representation"

        context.user_data = {
            "current_event": event,
        }

        prefix_text = "This is a prefix text"

        # Call the function
        await datetime_menu(update, context, prefix_text=prefix_text)

        # Check that the text includes the prefix
        call_args = update.callback_query.edit_message_text.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert prefix_text in kwargs["text"]
        assert "Event full representation" in kwargs["text"]

    @pytest.mark.asyncio
    async def test_datetime_menu_with_new_message_and_prefix(
        self, mock_update, mock_context
    ):
        """Test the datetime_menu function with new_message=True and prefix text."""
        # Setup
        update = mock_update
        context = mock_context
        update.callback_query = AsyncMock()
        update.effective_user = AsyncMock()

        event = MagicMock()
        event.occurrence = Occurrence.WITHIN_DAY
        event.time = "10:00"
        event.end_time = None
        event.date = "2023-01-01"
        event.end_date = None
        event.get_full_repr.return_value = "Event full representation"

        context.user_data = {
            "current_event": event,
        }

        prefix_text = "This is a prefix text"

        # Call the function
        await datetime_menu(update, context, prefix_text=prefix_text, new_message=True)

        # Check that the text is just the prefix (not including the event representation)
        call_args = update.effective_user.send_message.call_args
        assert call_args is not None
        kwargs = call_args[1]
        assert kwargs["text"] == prefix_text
        assert "Event full representation" not in kwargs["text"]

    def test_construct_back_button_default(self):
        """Test the construct_back_button function with default state."""
        # Call the function
        result = construct_back_button()

        # Assertions
        assert "reply_markup" in result
        keyboard = result["reply_markup"].inline_keyboard
        assert len(keyboard) == 1
        assert len(keyboard[0]) == 1
        assert keyboard[0][0].text == "🔙"
        assert keyboard[0][0].callback_data == State.BACK.name

    def test_construct_back_button_custom_state(self):
        """Test the construct_back_button function with a custom state."""
        # Call the function
        result = construct_back_button(State.CALENDAR_MENU)

        # Assertions
        assert "reply_markup" in result
        keyboard = result["reply_markup"].inline_keyboard
        assert len(keyboard) == 1
        assert len(keyboard[0]) == 1
        assert keyboard[0][0].text == "🔙"
        assert keyboard[0][0].callback_data == State.CALENDAR_MENU.name

    def test_events_menu_with_many_events(self, mock_python_calendar):
        """Test the events_menu function with more than 5 events."""
        # Setup
        from datetime import date

        this_week = date(2023, 1, 1)

        # Create mock events (more than 5 to trigger the break)
        events = []
        for i in range(10):
            event = MagicMock()
            event.date = this_week
            event.end_date = None
            event.get_title.return_value = f"Event {i+1}"
            events.append((i + 1, event))

        # Call the function
        result = events_menu(events)

        # Assertions
        assert "text" in result
        assert "reply_markup" in result

        # Check that the keyboard has the expected buttons
        keyboard = result["reply_markup"].inline_keyboard

        # Check that we only have 5 event buttons (due to the break)
        event_buttons = [
            button
            for row in keyboard
            for button in row
            if button.callback_data.startswith(f"{State.EVENT.name}:")
        ]
        assert len(event_buttons) == 5

        # Check for Search button
        assert any(
            button.text == "🔍 Search"
            and button.callback_data == State.EVENT_FINDING.name
            for row in keyboard
            for button in row
        )

        # Check for Back button
        assert any(
            button.text == "🔙" and button.callback_data == State.CALENDAR_MENU.name
            for row in keyboard
            for button in row
        )

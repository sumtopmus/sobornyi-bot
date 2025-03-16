#!/usr/bin/env python

import logging
import os
import pickle
import shutil
import sys
from datetime import date, datetime, time

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from config import settings
from model import Calendar, Category, Day, Event, Occurrence
from tools.migration import DATA, MigrationTool


def create_test_data(test_dir: str) -> None:
    """Create test data for migration testing.

    Args:
        test_dir: Directory to create test data in
    """
    os.makedirs(test_dir, exist_ok=True)

    # Create a calendar with events
    calendar = Calendar()

    # Add some events
    event1 = Event(
        title="Test Event 1",
        emoji="🎉",
        description="This is a test event",
        occurrence=Occurrence.WITHIN_DAY,
        date=date(2023, 1, 1),
        time=time(12, 0),
        venue="Test Venue",
        location="https://maps.google.com",
        url="https://example.com",
        category=Category.GENERAL,
    )

    event2 = Event(
        title="Test Event 2",
        emoji="🎭",
        description="This is another test event",
        occurrence=Occurrence.REGULAR,
        days={Day.Monday, Day.Wednesday, Day.Friday},
        time=time(18, 30),
        venue="Another Venue",
        category=Category.RALLY,
    )

    event_id1 = calendar.add_event(event1)
    event_id2 = calendar.add_event(event2)

    # Create bot_data
    bot_data = {
        "calendar": calendar,
        "agenda": {
            "date": datetime.now().date().isoformat(),
            "image": "https://example.com/image.jpg",
        },
        "jobs": {},
        "cross-posts": {},
        "current_event": None,
    }

    # Create chat_data
    chat_data = {
        123456789: {
            "settings": {
                "notifications": True,
                "language": "en",
            }
        }
    }

    # Create user_data
    user_data = {
        987654321: {
            "name": "Test User",
            "preferences": {
                "timezone": "Europe/London",
            },
        }
    }

    # Save data
    with open(os.path.join(test_dir, "db_bot_data"), "wb") as f:
        pickle.dump(bot_data, f)

    with open(os.path.join(test_dir, "db_chat_data"), "wb") as f:
        pickle.dump(chat_data, f)

    with open(os.path.join(test_dir, "db_user_data"), "wb") as f:
        pickle.dump(user_data, f)

    print(f"Created test data in {test_dir}")
    print(f"Added events with IDs: {event_id1}, {event_id2}")


def create_old_format_data(test_dir: str) -> None:
    """Create test data in an old format for migration testing.

    Args:
        test_dir: Directory to create test data in
    """
    os.makedirs(test_dir, exist_ok=True)

    # Create a calendar with events in old format
    # This is a simplified example - you would need to adjust this
    # to match your actual old data format
    calendar_data = {
        "_Calendar__events": {
            0: {
                "title": "Old Format Event 1",
                "emoji": "🎉",
                "description": "This is an old format event",
                "occurrence": "WITHIN_DAY",  # String instead of enum
                "date": "2023-01-01",  # String instead of date object
                "time": "12:00:00",  # String instead of time object
                "venue": "Old Venue",
                "location": "https://maps.google.com",
                "url": "https://example.com",
                "category": "GENERAL",  # String instead of enum
                "days": [],  # Empty list instead of set
            },
            1: {
                "title": "Old Format Event 2",
                "emoji": "🎭",
                "description": "This is another old format event",
                "occurrence": "REGULAR",  # String instead of enum
                "days": [
                    "Monday",
                    "Wednesday",
                    "Friday",
                ],  # List of strings instead of set of enums
                "time": "18:30:00",  # String instead of time object
                "venue": "Another Old Venue",
                "category": "RALLY",  # String instead of enum
            },
        },
        "_Calendar__next_id": 2,
    }

    # Create bot_data with old format calendar
    bot_data = {
        "calendar": calendar_data,
        "agenda": {"date": "2023-01-01", "image": "https://example.com/image.jpg"},
        "jobs": {},
        "cross-posts": {},
        "current_event": {
            "title": "Current Event",
            "emoji": "🎯",
            "description": "This is the current event",
            "occurrence": "WITHIN_DAY",
            "date": "2023-01-02",
            "time": "14:00:00",
            "venue": "Current Venue",
            "category": "GENERAL",
        },
    }

    # Create chat_data
    chat_data = {
        123456789: {
            "settings": {
                "notifications": True,
                "language": "en",
            }
        }
    }

    # Create user_data
    user_data = {
        987654321: {
            "name": "Test User",
            "preferences": {
                "timezone": "Europe/London",
            },
        }
    }

    # Save data
    with open(os.path.join(test_dir, "db_bot_data"), "wb") as f:
        pickle.dump(bot_data, f)

    with open(os.path.join(test_dir, "db_chat_data"), "wb") as f:
        pickle.dump(chat_data, f)

    with open(os.path.join(test_dir, "db_user_data"), "wb") as f:
        pickle.dump(user_data, f)

    print(f"Created old format test data in {test_dir}")


def inspect_data(data_path: str) -> None:
    """Inspect the data in a directory.

    Args:
        data_path: Path to the data directory
    """
    print(f"\nInspecting data in {data_path}:")

    # Load bot_data
    bot_data_path = os.path.join(data_path, "db_bot_data")
    if os.path.exists(bot_data_path):
        try:
            with open(bot_data_path, "rb") as f:
                bot_data = pickle.load(f)

            print("\nBot Data:")
            print(f"  Keys: {list(bot_data.keys())}")

            if "calendar" in bot_data:
                calendar = bot_data["calendar"]
                if isinstance(calendar, Calendar):
                    print("  Calendar is a Calendar object")
                    events = list(calendar.items())
                    print(f"  Number of events: {len(events)}")
                    for event_id, event in events:
                        print(
                            f"    Event {event_id}: {event.title} ({type(event).__name__})"
                        )
                        print(
                            f"      Date: {event.date} ({type(event.date).__name__ if event.date else None})"
                        )
                        print(
                            f"      Time: {event.time} ({type(event.time).__name__ if event.time else None})"
                        )
                        print(
                            f"      Category: {event.category} ({type(event.category).__name__})"
                        )
                        print(
                            f"      Occurrence: {event.occurrence} ({type(event.occurrence).__name__})"
                        )
                        if event.days:
                            print(
                                f"      Days: {event.days} ({type(event.days).__name__})"
                            )
                else:
                    print(f"  Calendar is a {type(calendar).__name__}")
                    if isinstance(calendar, dict):
                        print(f"  Calendar keys: {list(calendar.keys())}")

            if "current_event" in bot_data:
                current_event = bot_data["current_event"]
                if current_event:
                    print("\n  Current Event:")
                    if isinstance(current_event, Event):
                        print(f"    Title: {current_event.title}")
                        print(f"    Type: {type(current_event).__name__}")
                    else:
                        print(f"    Type: {type(current_event).__name__}")
                        print(f"    Data: {current_event}")
                else:
                    print("  Current Event: None")

            if "agenda" in bot_data:
                print("\n  Agenda:")
                print(f"    {bot_data['agenda']}")
        except Exception as e:
            print(f"Error loading bot data: {e}")
    else:
        print(f"No bot data found at {bot_data_path}")

    # Load chat_data
    chat_data_path = os.path.join(data_path, "db_chat_data")
    if os.path.exists(chat_data_path):
        try:
            with open(chat_data_path, "rb") as f:
                chat_data = pickle.load(f)

            print("\nChat Data:")
            print(f"  Number of chats: {len(chat_data)}")
            for chat_id, chat in chat_data.items():
                print(f"  Chat {chat_id}: {chat}")
        except Exception as e:
            print(f"Error loading chat data: {e}")
    else:
        print(f"No chat data found at {chat_data_path}")

    # Load user_data
    user_data_path = os.path.join(data_path, "db_user_data")
    if os.path.exists(user_data_path):
        try:
            with open(user_data_path, "rb") as f:
                user_data = pickle.load(f)

            print("\nUser Data:")
            print(f"  Number of users: {len(user_data)}")
            for user_id, user in user_data.items():
                print(f"  User {user_id}: {user}")
        except Exception as e:
            print(f"Error loading user data: {e}")
    else:
        print(f"No user data found at {user_data_path}")


def main() -> None:
    """Run the migration test."""
    # Create test directories
    test_dir = os.path.join("debug", "test_data")
    old_format_dir = os.path.join(test_dir, "old_format")
    new_format_dir = os.path.join(test_dir, "new_format")
    migrated_dir = os.path.join(test_dir, "migrated")

    # Clean up previous test data
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    # Create directories
    os.makedirs(old_format_dir, exist_ok=True)
    os.makedirs(new_format_dir, exist_ok=True)
    os.makedirs(migrated_dir, exist_ok=True)

    # Create test data
    create_test_data(new_format_dir)
    create_old_format_data(old_format_dir)

    # Inspect the data before migration
    inspect_data(old_format_dir)

    # Run migration
    migration_tool = MigrationTool(
        source_path=os.path.join(old_format_dir, "db"),  # Source path prefix
        target_path=os.path.join(migrated_dir, "db"),  # Target path prefix
        backup=True,
        log_level=logging.INFO,
        console_logging=True,
    )

    # Run migrations
    print("\nRunning migrations...")
    success = migration_tool.migrate(DATA.ALL)

    # Print migration results
    print(f"\nMigration results:")
    print(f"  All data: {'Success' if success else 'Failed'}")

    # Inspect the data after migration
    inspect_data(migrated_dir)

    # Compare with new format data
    print("\nComparing with new format data:")
    inspect_data(new_format_dir)


if __name__ == "__main__":
    main()

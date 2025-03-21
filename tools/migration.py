#!/usr/bin/env python

import argparse
import copy
import logging
import os
import pickle
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from config import settings
from model import Calendar, Category, Day, Event, Occurrence

DATA = Enum("DATA", ["ALL", "BOT", "CHAT", "USER"])


class VersionedUnpickler(pickle.Unpickler):
    """Custom unpickler that handles class relocations and missing classes.

    This unpickler is designed to handle cases where class structures have changed
    between the time the data was pickled and when it's being unpickled. It provides
    mechanisms to:

    1. Map old class paths to new ones (for relocated classes)
    2. Handle missing classes by creating placeholder classes
    3. Special handling for enum types

    Usage examples:

    # Basic usage
    with open('data.pickle', 'rb') as f:
        unpickler = VersionedUnpickler(f, logger)
        data = unpickler.load()

    # Adding custom class mappings
    with open('data.pickle', 'rb') as f:
        unpickler = VersionedUnpickler(f, logger)
        unpickler.add_class_mapping('old_module.OldClass', 'new_module', 'NewClass')
        data = unpickler.load()
    """

    def __init__(self, file_obj, logger):
        super().__init__(file_obj)
        self.logger = logger
        # Map old class paths to new ones
        self.class_mapping = {
            # Add mappings for classes that have moved or been restructured
            # Format: 'old_module.old_class': ('new_module', 'new_class')
            "model.Calendar.Occurrence": ("model", "Occurrence"),
            # Add more mappings as needed for other relocated classes
        }

        # Initialize the attribute mapping dictionary
        self.attr_mapping = {
            "model.Calendar": {
                "_Calendar__events": "_events",
                "_Calendar__next_id": "_next_id",
            }
        }

    def add_class_mapping(self, old_path: str, new_module: str, new_name: str) -> None:
        """Add a class mapping to the unpickler.

        Args:
            old_path: Old class path in the format 'module.class'
            new_module: New module name
            new_name: New class name
        """
        self.class_mapping[old_path] = (new_module, new_name)
        self.logger.info(f"Added class mapping: {old_path} -> {new_module}.{new_name}")

    def add_attr_mapping(self, class_path: str, old_attr: str, new_attr: str) -> None:
        """Add an attribute mapping for a class.

        Args:
            class_path: Class path in the format 'module.class'
            old_attr: Old attribute name
            new_attr: New attribute name
        """
        if class_path not in self.attr_mapping:
            self.attr_mapping[class_path] = {}
        self.attr_mapping[class_path][old_attr] = new_attr
        self.logger.info(
            f"Added attribute mapping for {class_path}: {old_attr} -> {new_attr}"
        )

    def remap_attributes(self, obj) -> None:
        """Remap attributes in an object based on attribute mappings.

        Args:
            obj: Object to remap attributes in
        """
        if not hasattr(obj, "__class__"):
            return

        class_path = f"{obj.__class__.__module__}.{obj.__class__.__name__}"
        if class_path in self.attr_mapping:
            attrs_to_remap = self.attr_mapping[class_path]
            for old_attr, new_attr in attrs_to_remap.items():
                if hasattr(obj, old_attr) and not hasattr(obj, new_attr):
                    setattr(obj, new_attr, getattr(obj, old_attr))
                    self.logger.info(
                        f"Remapped attribute {old_attr} to {new_attr} in {class_path}"
                    )

    def find_class(self, module, name):
        # Check if this class has been relocated
        old_path = f"{module}.{name}"
        self.logger.info(f"Checking for class mapping: {old_path}")
        if old_path in self.class_mapping:
            new_module, new_name = self.class_mapping[old_path]
            self.logger.info(f"Remapping {old_path} to {new_module}.{new_name}")
            try:
                # Try to import the class from its new location
                __import__(new_module)
                cls = getattr(sys.modules[new_module], new_name)
                self.logger.info(
                    f"Successfully remapped {old_path} to {new_module}.{new_name}"
                )
                return cls
            except (ImportError, AttributeError) as e:
                self.logger.warning(f"Failed to remap {old_path}: {e}")

        # Try the normal way
        try:
            return super().find_class(module, name)
        except (AttributeError, ImportError, ModuleNotFoundError) as e:
            self.logger.warning(f"Could not find class {module}.{name}: {e}")

            # If it's an enum, try to find or create it
            if name in ["Occurrence", "Category", "Day"]:
                try:
                    # Try to import from the model module
                    __import__("model")
                    if hasattr(sys.modules["model"], name):
                        self.logger.info(f"Found {name} in model module")
                        return getattr(sys.modules["model"], name)
                except (ImportError, AttributeError):
                    pass

            # Create a placeholder class as a last resort
            self.logger.warning(f"Creating placeholder for {module}.{name}")
            return type(name, (), {"__module__": module})


class MigrationTool:
    """Tool for migrating persistent data to newer model structures."""

    def __init__(
        self,
        source_path: str,
        target_path: Optional[str] = None,
        backup: bool = True,
        log_level: int = logging.INFO,
        console_logging: bool = True,
    ):
        """Initialize the migration tool.

        Args:
            source_path: Path to the source data directory
            target_path: Path to the target data directory (if None, will use the source path)
            backup: Whether to create a backup of the source data
            log_level: Logging level (default: INFO)
            console_logging: Whether to log to console (default: True)
        """
        self.source_path = source_path
        self.target_path = target_path or source_path
        self.backup = backup
        self.logger = self._setup_logger(log_level, console_logging)

        # Define class and attribute mappings to be used consistently across all methods
        self.class_mappings = {
            "model.Calendar.Occurrence": ("model", "Occurrence"),
            "model.calendar.Category": ("model", "Category"),
            "model.calendar.Day": ("model", "Day"),
            "model.calendar.Occurrence": ("model", "Occurrence"),
            "model.calendar.Event": ("model", "Event"),
            "model.calendar.Calendar": ("model", "Calendar"),
        }

        self.attr_mappings = {
            "model.Calendar": {
                "_Calendar__events": "_events",
                "_Calendar__next_id": "_next_id",
            }
        }

    def _setup_logger(self, log_level: int, console_logging: bool) -> logging.Logger:
        """Set up logging for the migration tool.

        Args:
            log_level: Logging level
            console_logging: Whether to log to console

        Returns:
            Configured logger
        """
        # Create logger
        logger = logging.getLogger("migration")
        logger.setLevel(log_level)

        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(settings.LOG_PATH)
        os.makedirs(log_dir, exist_ok=True)

        # File handler
        migration_log_path = os.path.join(log_dir, "migration.log")
        file_handler = logging.FileHandler(migration_log_path)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler (optional)
        if console_logging:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter("%(levelname)s: %(message)s")
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        return logger

    def _create_backup(self, file_path: str) -> str:
        """Create a backup of a file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file
        """
        if not os.path.exists(file_path):
            self.logger.warning(f"File {file_path} does not exist, skipping backup")
            return ""

        backup_dir = os.path.join(os.path.dirname(file_path), "backup")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}")

        with open(file_path, "rb") as source_file:
            with open(backup_path, "wb") as backup_file:
                backup_file.write(source_file.read())

        self.logger.info(f"Created backup at {backup_path}")
        return backup_path

    def _create_unpickler(self, file_obj, additional_mappings=None):
        """Create a VersionedUnpickler with optional additional mappings.

        Args:
            file_obj: File object to unpickle from
            additional_mappings: Optional dictionary of additional class mappings
                                 in the format {'old_module.old_class': ('new_module', 'new_class')}

        Returns:
            Configured VersionedUnpickler
        """
        unpickler = VersionedUnpickler(file_obj, self.logger)

        # Add class mappings defined in __init__
        for old_path, (new_module, new_name) in self.class_mappings.items():
            unpickler.add_class_mapping(old_path, new_module, new_name)

        # Add any additional mappings
        if additional_mappings:
            for old_path, (new_module, new_name) in additional_mappings.items():
                unpickler.add_class_mapping(old_path, new_module, new_name)

        # Add attribute mappings defined in __init__
        for class_path, attr_map in self.attr_mappings.items():
            for old_attr, new_attr in attr_map.items():
                unpickler.add_attr_mapping(class_path, old_attr, new_attr)

        return unpickler

    def _load_data(self, file_path: str, additional_mappings=None) -> Any:
        """Load data from a pickle file.

        Args:
            file_path: Path to the pickle file
            additional_mappings: Optional dictionary of additional class mappings
                                 in the format {'old_module.old_class': ('new_module', 'new_class')}

        Returns:
            The loaded data
        """
        if not os.path.exists(file_path):
            self.logger.warning(f"File {file_path} does not exist")
            return None

        # Use only the custom unpickler approach
        try:
            with open(file_path, "rb") as f:
                self.logger.info(
                    f"Loading data from {file_path} using custom unpickler"
                )
                unpickler = self._create_unpickler(f, additional_mappings)
                data = unpickler.load()

                # Apply attribute remapping recursively
                try:
                    self._remap_attributes_recursively(data)
                except Exception as remap_error:
                    self.logger.warning(
                        f"Error during attribute remapping: {remap_error}"
                    )
                    self.logger.warning("Continuing with partially remapped data")

                self.logger.info(f"Successfully loaded data from {file_path}")
                return data
        except Exception as e:
            self.logger.error(f"Failed to load data from {file_path}: {e}")
            # Fall back to standard pickle load as a last resort
            try:
                self.logger.warning("Attempting fallback to standard pickle load...")
                with open(file_path, "rb") as f:
                    data = pickle.load(f)
                self.logger.info("Successfully loaded data using standard pickle")
                return data
            except Exception as fallback_error:
                self.logger.error(f"Fallback loading also failed: {fallback_error}")
                raise e

    def _remap_attributes_recursively(self, obj, visited=None):
        """Recursively remap attributes in an object and its children.

        Args:
            obj: Object to remap attributes in
            visited: Set of already visited objects to prevent infinite recursion
        """
        if obj is None:
            return

        # Initialize visited set if not provided
        if visited is None:
            visited = set()

        # Check if object has already been visited to prevent infinite recursion
        obj_id = id(obj)
        if obj_id in visited:
            return

        # Add this object to visited set
        visited.add(obj_id)

        # Apply attribute remapping to the object
        self._apply_attribute_remapping(obj)

        # Recursively process dictionaries
        if isinstance(obj, dict):
            for key, value in obj.items():
                if id(value) not in visited:
                    self._remap_attributes_recursively(value, visited)

        # Recursively process lists and tuples
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                if id(item) not in visited:
                    self._remap_attributes_recursively(item, visited)

        # Recursively process object attributes
        elif hasattr(obj, "__dict__"):
            # Get the list of attributes safely
            try:
                attributes = list(obj.__dict__.keys())
            except (AttributeError, TypeError):
                # If we can't get attributes through __dict__, try dir()
                attributes = [
                    attr
                    for attr in dir(obj)
                    if not attr.startswith("__")
                    and not callable(getattr(obj, attr, None))
                ]

            for attr_name in attributes:
                # Skip special Python attributes
                if attr_name.startswith("__"):
                    continue

                try:
                    attr_value = getattr(obj, attr_name)
                    # Only process non-callable attributes
                    if not callable(attr_value) and id(attr_value) not in visited:
                        self._remap_attributes_recursively(attr_value, visited)
                except (AttributeError, TypeError) as e:
                    # Log and continue if we encounter attribute access errors
                    self.logger.debug(f"Skipping attribute {attr_name}: {e}")
                    continue

    def _apply_attribute_remapping(self, obj):
        """Apply attribute remapping to a single object.

        Args:
            obj: Object to remap attributes in
        """
        if obj is None:
            return

        if not hasattr(obj, "__class__"):
            return

        try:
            class_path = f"{obj.__class__.__module__}.{obj.__class__.__name__}"

            # Use the attribute mappings defined in __init__
            if class_path in self.attr_mappings:
                attrs_to_remap = self.attr_mappings[class_path]
                for old_attr, new_attr in attrs_to_remap.items():
                    try:
                        if hasattr(obj, old_attr) and not hasattr(obj, new_attr):
                            # Get the value from the old attribute
                            value = getattr(obj, old_attr)
                            # Set the new attribute
                            setattr(obj, new_attr, value)
                            self.logger.info(
                                f"Remapped attribute {old_attr} to {new_attr} in {class_path}"
                            )
                    except (AttributeError, TypeError) as e:
                        self.logger.warning(
                            f"Error remapping attribute {old_attr} to {new_attr} in {class_path}: {e}"
                        )
        except Exception as e:
            self.logger.warning(f"Error determining class path for object: {e}")
            return

    def _save_data(self, data: Any, file_path: str) -> bool:
        """Save data to a pickle file.

        Args:
            data: Data to save
            file_path: Path to the pickle file

        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                pickle.dump(data, f)
            self.logger.info(f"Saved data to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving data to {file_path}: {e}")
            return False

    def _migrate_event(self, event_data: Dict[str, Any]) -> Event:
        """Migrate an event from old format to new format.

        Args:
            event_data: Event data in old format

        Returns:
            Event in new format
        """
        # Make a copy of the event data to avoid modifying the original
        event_data_copy = copy.deepcopy(event_data)

        # Convert string dates to datetime objects
        if isinstance(event_data_copy.get("date"), str):
            try:
                event_data_copy["date"] = datetime.fromisoformat(
                    event_data_copy["date"]
                ).date()
            except (ValueError, TypeError):
                event_data_copy["date"] = None

        if isinstance(event_data_copy.get("end_date"), str):
            try:
                event_data_copy["end_date"] = datetime.fromisoformat(
                    event_data_copy["end_date"]
                ).date()
            except (ValueError, TypeError):
                event_data_copy["end_date"] = None

        # Convert string times to time objects
        if isinstance(event_data_copy.get("time"), str):
            try:
                event_data_copy["time"] = datetime.fromisoformat(
                    event_data_copy["time"]
                ).time()
            except (ValueError, TypeError):
                event_data_copy["time"] = None

        if isinstance(event_data_copy.get("end_time"), str):
            try:
                event_data_copy["end_time"] = datetime.fromisoformat(
                    event_data_copy["end_time"]
                ).time()
            except (ValueError, TypeError):
                event_data_copy["end_time"] = None

        # Convert occurrence to the new Occurrence enum
        if "occurrence" in event_data_copy:
            occurrence = event_data_copy["occurrence"]

            # Handle string representation
            if isinstance(occurrence, str):
                try:
                    event_data_copy["occurrence"] = Occurrence[occurrence]
                except (KeyError, TypeError):
                    self.logger.warning(
                        f"Unknown occurrence string: {occurrence}, defaulting to WITHIN_DAY"
                    )
                    event_data_copy["occurrence"] = Occurrence.WITHIN_DAY

            # Handle old enum instances
            elif (
                hasattr(occurrence, "__module__")
                and occurrence.__module__ == "model.Calendar"
            ):
                # Get the name of the enum value and convert to new enum
                try:
                    occurrence_name = (
                        occurrence.name
                        if hasattr(occurrence, "name")
                        else str(occurrence)
                    )
                    event_data_copy["occurrence"] = Occurrence[occurrence_name]
                    self.logger.info(
                        f"Successfully converted old Calendar.Occurrence.{occurrence_name} to new Occurrence.{occurrence_name}"
                    )
                except (KeyError, AttributeError):
                    self.logger.warning(
                        f"Failed to convert old Occurrence enum, defaulting to WITHIN_DAY"
                    )
                    event_data_copy["occurrence"] = Occurrence.WITHIN_DAY

            # If it's already the correct enum type, keep it
            elif isinstance(occurrence, Occurrence):
                pass

            # Default case
            else:
                self.logger.warning(
                    f"Unknown occurrence type: {type(occurrence)}, defaulting to WITHIN_DAY"
                )
                event_data_copy["occurrence"] = Occurrence.WITHIN_DAY

        # Convert category string to enum
        if isinstance(event_data_copy.get("category"), str):
            try:
                event_data_copy["category"] = Category[event_data_copy["category"]]
            except (KeyError, TypeError):
                event_data_copy["category"] = Category.GENERAL

        # Convert days list to set of Day enums
        if isinstance(event_data_copy.get("days"), list):
            days_set = set()
            for day_name in event_data_copy["days"]:
                try:
                    days_set.add(Day[day_name])
                except (KeyError, TypeError):
                    pass
            event_data_copy["days"] = days_set
        elif not event_data_copy.get("days"):
            # Ensure days is a set if it doesn't exist or is None
            event_data_copy["days"] = set()

        # Handle any new fields that might have been added to the Event model
        # For example, if a new field 'priority' was added:
        # if "priority" not in event_data_copy:
        #     event_data_copy["priority"] = default_priority_value

        # Handle any renamed fields
        # For example, if 'location_url' was renamed to 'location':
        # if "location_url" in event_data_copy and "location" not in event_data_copy:
        #     event_data_copy["location"] = event_data_copy.pop("location_url")

        # Remove any fields that no longer exist in the Event model
        # Get the signature of the Event constructor
        from inspect import signature

        event_params = signature(Event.__init__).parameters
        # Remove fields that are not in the Event constructor
        keys_to_remove = [
            key
            for key in list(event_data_copy.keys())
            if key not in event_params and key != "self"
        ]
        for key in keys_to_remove:
            self.logger.warning(
                f"Removing field '{key}' from event data as it no longer exists in the Event model"
            )
            event_data_copy.pop(key, None)

        # Create and return the Event object
        try:
            return Event(**event_data_copy)
        except TypeError as e:
            self.logger.error(f"Error creating Event object: {e}")
            # Log the event data for debugging
            self.logger.error(f"Event data: {event_data_copy}")
            # Try to create a minimal Event object with just the required fields
            return Event(title=event_data_copy.get("title", "Unknown Event"))

    def _migrate_calendar(self, calendar_data: Any) -> Calendar:
        """Migrate a calendar from old format to new format.

        Args:
            calendar_data: Calendar data in old format

        Returns:
            Calendar in new format
        """
        self.logger.info(f"Calendar data type: {type(calendar_data)}")

        # Create a new Calendar object
        calendar = Calendar()

        # Handle Calendar class instance case
        if hasattr(calendar_data, "__class__"):
            self.logger.info(
                f"Handling Calendar class instance: {calendar_data.__class__.__name__}"
            )

            # Check for events attribute in various forms
            events = {}
            next_id = 0

            class_path = f"{calendar_data.__class__.__module__}.{calendar_data.__class__.__name__}"
            model_calendar_attrs = self.attr_mappings.get("model.Calendar", {})

            # Get events attribute using mappings
            events_attr = "_events"  # New attribute name
            old_events_attr = next(
                (old for old, new in model_calendar_attrs.items() if new == "_events"),
                None,
            )

            if hasattr(calendar_data, events_attr):
                self.logger.info(f"Found {events_attr} attribute on object")
                events = getattr(calendar_data, events_attr, {})
            elif old_events_attr and hasattr(calendar_data, old_events_attr):
                self.logger.info(f"Found {old_events_attr} attribute on object")
                events = getattr(calendar_data, old_events_attr, {})

            # Get next_id attribute using mappings
            next_id_attr = "_next_id"  # New attribute name
            old_next_id_attr = next(
                (old for old, new in model_calendar_attrs.items() if new == "_next_id"),
                None,
            )

            if hasattr(calendar_data, next_id_attr):
                next_id = getattr(calendar_data, next_id_attr, 0)
            elif old_next_id_attr and hasattr(calendar_data, old_next_id_attr):
                next_id = getattr(calendar_data, old_next_id_attr, 0)

            # Migrate events
            calendar._events = {}
            for event_id, event_data in events.items():
                try:
                    # If event_data is already an Event object, add it directly
                    if isinstance(event_data, Event):
                        calendar._events[event_id] = event_data
                    else:
                        # Otherwise, migrate the event data
                        migrated_event = self._migrate_event(event_data)
                        calendar._events[event_id] = migrated_event
                except Exception as e:
                    self.logger.error(f"Error migrating event {event_id}: {e}")

            calendar._next_id = next_id
        else:
            self.logger.warning(f"Unexpected calendar data type: {type(calendar_data)}")

        self.logger.info(
            f"Migrated calendar with {len(calendar._events)} events and next_id={calendar._next_id}"
        )
        return calendar

    def _convert_enums_in_dict(self, data: Any, visited=None) -> Any:
        """Recursively convert old enum values in dictionaries and lists.

        Args:
            data: Data structure that might contain old enum values
            visited: Set of already visited objects to prevent infinite recursion

        Returns:
            Data structure with converted enum values
        """
        if data is None:
            return None

        # Initialize visited set if not provided
        if visited is None:
            visited = set()

        # Check if object has already been visited to prevent infinite recursion
        obj_id = id(data)
        if obj_id in visited:
            return data

        # Add this object to visited set
        visited.add(obj_id)

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = self._convert_enums_in_dict(value, visited)
            return result
        elif isinstance(data, list):
            return [self._convert_enums_in_dict(item, visited) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._convert_enums_in_dict(item, visited) for item in data)
        # Check if it's an old Occurrence enum
        elif (
            hasattr(data, "__module__")
            and data.__module__ == "model.Calendar"
            and hasattr(data, "name")
        ):
            try:
                enum_name = data.name
                if enum_name in [e.name for e in Occurrence]:
                    self.logger.info(
                        f"Successfully converted old Occurrence.{enum_name} to new enum"
                    )
                    return Occurrence[enum_name]
                elif enum_name in [e.name for e in Category]:
                    self.logger.info(
                        f"Successfully converted old Category.{enum_name} to new enum"
                    )
                    return Category[enum_name]
                elif enum_name in [e.name for e in Day]:
                    self.logger.info(
                        f"Successfully converted old Day.{enum_name} to new enum"
                    )
                    return Day[enum_name]
            except (AttributeError, KeyError) as e:
                self.logger.warning(f"Failed to convert enum value: {e}")
        return data

    def _migrate_bot_data(self) -> bool:
        """Migrate bot data.

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Starting bot data migration")

        source_file = self.source_path + "_bot_data"
        target_file = self.target_path + "_bot_data"

        self.logger.info(f"Source path: {source_file}")
        self.logger.info(f"Target path: {target_file}")

        if self.backup:
            self._create_backup(source_file)

        # Use the class mappings already defined in __init__
        try:
            bot_data = self._load_data(source_file)
            if bot_data is None:
                self.logger.error("Bot data migration failed: Could not load data")
                return False

            # Make a deep copy to avoid modifying the original data
            try:
                migrated_bot_data = copy.deepcopy(bot_data)
            except Exception as copy_error:
                self.logger.warning(f"Error during deep copy: {copy_error}")
                self.logger.warning("Using original data instead of copy")
                migrated_bot_data = bot_data

            # Convert any old enum values in the entire data structure
            try:
                migrated_bot_data = self._convert_enums_in_dict(migrated_bot_data)
            except Exception as enum_error:
                self.logger.warning(f"Error converting enums: {enum_error}")
                self.logger.warning("Continuing with partially converted data")

            # Migrate calendar
            if "calendar" in migrated_bot_data:
                try:
                    migrated_bot_data["calendar"] = self._migrate_calendar(
                        migrated_bot_data["calendar"]
                    )
                    self.logger.info("Successfully migrated calendar")
                except Exception as e:
                    self.logger.error(f"Error migrating calendar: {e}")
                    self.logger.warning("Continuing without migrated calendar")
                    # Don't return False, try to continue with other data

            # Migrate agenda data
            if "agenda" in migrated_bot_data:
                try:
                    # Convert date strings to datetime objects if needed
                    if isinstance(migrated_bot_data["agenda"].get("date"), str):
                        try:
                            migrated_bot_data["agenda"]["date"] = (
                                datetime.fromisoformat(
                                    migrated_bot_data["agenda"]["date"]
                                )
                                .date()
                                .isoformat()
                            )
                        except (ValueError, TypeError):
                            pass  # Keep as string if conversion fails

                    self.logger.info("Successfully migrated agenda data")
                except Exception as e:
                    self.logger.error(f"Error migrating agenda data: {e}")
                    # Don't return False, continue with other migrations

            # Migrate cross-posts data
            # This appears to be a mapping of message IDs, so no special migration needed
            if "cross-posts" in migrated_bot_data:
                try:
                    self.logger.info("Successfully processed cross-posts data")
                except Exception as e:
                    self.logger.error(f"Error processing cross-posts data: {e}")
                    # Continue with other migrations

            # Migrate jobs data
            if "jobs" in migrated_bot_data:
                try:
                    # If there are any datetime objects in the jobs data, ensure they're serializable
                    for job_name, job_data in migrated_bot_data.get("jobs", {}).items():
                        if "time" in job_data and isinstance(
                            job_data["time"], datetime
                        ):
                            # Ensure datetime objects are serializable
                            pass  # Already handled by pickle

                    self.logger.info("Successfully migrated jobs data")
                except Exception as e:
                    self.logger.error(f"Error migrating jobs data: {e}")
                    # Don't return False here, continue with other migrations

            # Migrate current_event data
            if "current_event" in migrated_bot_data:
                try:
                    if migrated_bot_data["current_event"] is not None:
                        # If it's an Event object, no need to migrate
                        if not isinstance(migrated_bot_data["current_event"], Event):
                            # Otherwise, migrate the event data
                            migrated_bot_data["current_event"] = self._migrate_event(
                                migrated_bot_data["current_event"]
                            )

                    self.logger.info("Successfully migrated current_event data")
                except Exception as e:
                    self.logger.error(f"Error migrating current_event data: {e}")
                    # Don't return False here, continue with other migrations

            # Add version info
            if "version" not in migrated_bot_data:
                migrated_bot_data["version"] = "1.0.0"
                self.logger.info("Added missing version field with default value 1.0.0")
            else:
                self.logger.info(
                    f"Version field already exists: {migrated_bot_data['version']}"
                )

            success = self._save_data(migrated_bot_data, target_file)
            if success:
                self.logger.info("Bot data migration completed successfully")
            else:
                self.logger.error("Bot data migration failed when saving data")
            return success
        except Exception as e:
            self.logger.error(f"Unexpected error during bot data migration: {e}")
            return False

    def _migrate_chat_data(self) -> bool:
        """Migrate chat data.

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Starting chat data migration")

        source_file = self.source_path + "_chat_data"
        target_file = self.target_path + "_chat_data"

        self.logger.info(f"Source path: {source_file}")
        self.logger.info(f"Target path: {target_file}")

        if self.backup:
            self._create_backup(source_file)

        # Use the class mappings already defined in __init__
        chat_data = self._load_data(source_file)
        if chat_data is None:
            self.logger.error("Chat data migration failed: Could not load data")
            return False

        # Make a deep copy to avoid modifying the original data
        migrated_chat_data = copy.deepcopy(chat_data)

        # TODO: Implement chat data migration logic here
        # This is a placeholder for actual migration logic

        success = self._save_data(migrated_chat_data, target_file)
        if success:
            self.logger.info("Chat data migration completed successfully")
        else:
            self.logger.error("Chat data migration failed when saving data")
        return success

    def _migrate_user_data(self) -> bool:
        """Migrate user data.

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Starting user data migration")

        source_file = self.source_path + "_user_data"
        target_file = self.target_path + "_user_data"

        self.logger.info(f"Source path: {source_file}")
        self.logger.info(f"Target path: {target_file}")

        if self.backup:
            self._create_backup(source_file)

        # Use the class mappings already defined in __init__
        user_data = self._load_data(source_file)
        if user_data is None:
            self.logger.error("User data migration failed: Could not load data")
            return False

        # Make a deep copy to avoid modifying the original data
        migrated_user_data = copy.deepcopy(user_data)

        # TODO: Implement user data migration logic here
        # This is a placeholder for actual migration logic

        success = self._save_data(migrated_user_data, target_file)
        if success:
            self.logger.info("User data migration completed successfully")
        else:
            self.logger.error("User data migration failed when saving data")
        return success

    def _migrate_all(self) -> bool:
        """Migrate all data.

        Returns:
            Tuple of booleans indicating success of bot_data, chat_data, and user_data migrations
        """
        self.logger.info("Starting migration of all data")
        self.logger.info(f"Source path: {self.source_path}")
        self.logger.info(f"Target path: {self.target_path}")

        bot_success = self._migrate_bot_data()
        chat_success = self._migrate_chat_data()
        user_success = self._migrate_user_data()

        all_success = bot_success and chat_success and user_success
        if all_success:
            self.logger.info("All data migration completed successfully")
        else:
            failed = []
            if not bot_success:
                failed.append("bot data")
            if not chat_success:
                failed.append("chat data")
            if not user_success:
                failed.append("user data")
            self.logger.error(f"Migration failed for: {', '.join(failed)}")
            print(f"Migration failed for: {', '.join(failed)}")

        return all_success

    def migrate(self, data: DATA) -> bool:
        """Migrate data.

        Args:
            data: Data to migrate

        Returns:
            True if successful, False otherwise
        """
        success = False
        if data == DATA.BOT:
            success = self._migrate_bot_data()
        elif data == DATA.CHAT:
            success = self._migrate_chat_data()
        elif data == DATA.USER:
            success = self._migrate_user_data()
        else:
            success = self._migrate_all()

        if success:
            self.logger.info(
                f"Migration of {data.name.lower()} data completed successfully"
            )
        else:
            self.logger.error(f"Migration of {data.name.lower()} data failed")

        return success


def main() -> None:
    """Run the migration tool."""
    parser = argparse.ArgumentParser(
        description="Migrate persistent data to newer model structures"
    )
    parser.add_argument(
        "--source", default=settings.DB_PATH, help="Path to the source data directory"
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Path to the target data directory (if different from source)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backups of the source data",
    )
    parser.add_argument("--bot-only", action="store_true", help="Only migrate bot data")
    parser.add_argument(
        "--chat-only", action="store_true", help="Only migrate chat data"
    )
    parser.add_argument(
        "--user-only", action="store_true", help="Only migrate user data"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--no-console",
        action="store_true",
        help="Disable console logging (log to file only)",
    )

    args = parser.parse_args()

    # Create migration tool with appropriate log level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    migration_tool = MigrationTool(
        args.source, args.target, not args.no_backup, log_level, not args.no_console
    )

    # Run migration based on command-line arguments
    if args.bot_only:
        success = migration_tool.migrate(DATA.BOT)
    elif args.chat_only:
        success = migration_tool.migrate(DATA.CHAT)
    elif args.user_only:
        success = migration_tool.migrate(DATA.USER)
    else:
        success = migration_tool.migrate(DATA.ALL)

    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

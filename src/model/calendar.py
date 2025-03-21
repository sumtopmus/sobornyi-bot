from typing import Dict, List, Optional

from telegram.helpers import escape_markdown

from .event import Category, Event
from .utils import next_week, this_week


class Calendar:
    def __init__(self):
        self._events: Dict[int, Event] = {}
        self._next_id: int = 0

    def add_event(self, event: Event) -> int:
        event_id = self._next_id
        self._events[event_id] = event
        self._next_id += 1
        return event_id

    def delete_event(self, event: Event) -> bool:
        for event_id, calendar_event in self._events.items():
            if calendar_event == event:
                del self._events[event_id]
                return True
        return False

    def get_event(self, event_id: int) -> Optional[Event]:
        return self._events.get(event_id)

    def get_nearest_events(self) -> List[Event]:
        nearest_events = []
        for _, event in self._events.items():
            if (
                not event.date
                or this_week() <= event.date < next_week()
                or (event.end_date and event.date < this_week() <= event.end_date)
            ):
                nearest_events.append(event)
        sorted_nearest_events = sorted(
            nearest_events, key=lambda event: (event.date is not None, event.date)
        )
        return sorted_nearest_events

    def get_future_events(self) -> List[Event]:
        future_events = []
        for _, event in self._events.items():
            if event.date and next_week() <= event.date:
                future_events.append(event)
        sorted_future_events = sorted(future_events, key=lambda event: event.date)
        return sorted_future_events

    def get_simple_agenda(
        self, events: List[Event], category: Category = None
    ) -> Optional[str]:
        filtered_events = events
        if category is not None:
            filtered_events = [event for event in events if event.category == category]
        if not filtered_events:
            return None
        return "\n".join([event.get_title_repr() for event in filtered_events])

    def get_urls_by_category(
        self, events: List[Event], category: Category = None
    ) -> Optional[str]:
        filtered_events = events
        if category is not None:
            filtered_events = [event for event in events if event.category == category]
        urls = [
            url for event in filtered_events if (url := event.get_url()) is not None
        ]
        if not urls:
            return None
        return "\n\n".join(urls)

    def get_nearest_agenda(
        self, events: List[Event], category: Category = None
    ) -> Optional[str]:
        filtered_events = events
        if category is not None:
            filtered_events = [event for event in events if event.category == category]
        if not filtered_events:
            return None
        return "\n".join([event.get_current_repr() for event in filtered_events])

    def get_future_agenda(self, events: List[Event]) -> Optional[str]:
        event_reprs = [
            repr for event in events if (repr := event.get_future_repr()) is not None
        ]
        if not event_reprs:
            return None
        return "\n".join(event_reprs)

    def get_agenda(self) -> str:
        result = f"*Порядок тижневий*\n\n"
        nearest_events = self.get_nearest_events()
        events_repr = self.get_nearest_agenda(nearest_events, Category.GENERAL)
        if events_repr:
            result += f"*🎟 Заходи:*\n{events_repr}\n\n"
        events_repr = self.get_nearest_agenda(nearest_events, Category.RALLY)
        if events_repr:
            result += f"*📢 Ралі:*\n{events_repr}\n\n"
        events_repr = self.get_future_agenda(self.get_future_events())
        if events_repr:
            result += f"*📰 Анонси:*\n{events_repr}\n\n"
        events_repr = self.get_simple_agenda(nearest_events, Category.FUNDRAISER)
        if events_repr:
            result += f"*💰 Збори коштів:*\n{events_repr}\n\n"
        events_repr = self.get_simple_agenda(nearest_events, Category.VOLUNTEER)
        if events_repr:
            result += f"*🤲 Волонтерство:*\n{events_repr}\n\n"
        result += "_#agenda_"
        return result

    def get_agenda_as_urls(self) -> str:
        result = ""
        nearest_events = self.get_nearest_events()
        events_repr = self.get_urls_by_category(nearest_events, Category.GENERAL)
        if events_repr:
            result += f"🎟 Заходи:\n{events_repr}\n\n"
        events_repr = self.get_urls_by_category(nearest_events, Category.RALLY)
        if events_repr:
            result += f"📢 Ралі:\n{events_repr}\n\n"
        events_repr = self.get_urls_by_category(self.get_future_events())
        if events_repr:
            result += f"📰 Анонси:\n{events_repr}\n\n"
        events_repr = self.get_urls_by_category(nearest_events, Category.FUNDRAISER)
        if events_repr:
            result += f"💰 Збори коштів:\n{events_repr}\n\n"
        events_repr = self.get_urls_by_category(nearest_events, Category.VOLUNTEER)
        if events_repr:
            result += f"🤲 Волонтерство:\n{events_repr}"
        return escape_markdown(result)

    def remove_past_events(self) -> bool:
        events_to_remove = []
        for event_id, event in self._events.items():
            if event.date and event.date < this_week():
                if not event.end_date or event.end_date < this_week():
                    events_to_remove.append(event_id)

        for event_id in events_to_remove:
            del self._events[event_id]
        return len(events_to_remove) > 0

    def __getitem__(self, event_id: int) -> Optional[Event]:
        return self._events[event_id]

    def __setitem__(self, event_id: int, event: Event):
        self._events[event_id] = event

    def __delitem__(self, event_id: int):
        del self._events[event_id]

    def __contains__(self, event_id: int) -> bool:
        return event_id in self._events

    def __iter__(self):
        return iter(self._events)

    def items(self):
        return self._events.items()

    def values(self):
        return self._events.values()

    def keys(self):
        return self._events.keys()

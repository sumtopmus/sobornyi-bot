from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
import re
from typing import Dict, List, Optional, Set

from format import clock, link, weekday


Category = Enum(
    "Category",
    [
        "GENERAL",
        "FUNDRAISER",
        "RALLY",
        "VOLUNTEER",
    ],
)

Occurrence = Enum("Occurrence", ["WITHIN_DAY", "WITHIN_DAYS", "REGULAR"])


class Day(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


@dataclass
class Event:
    title: str
    emoji: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    occurrence: Occurrence = field(default=Occurrence.WITHIN_DAY)
    date: Optional[datetime.date] = field(default=None)
    time: Optional[datetime.time] = field(default=None)
    end_date: Optional[str] = field(default=None)
    end_time: Optional[str] = field(default=None)
    days: Set[Day] = field(default_factory=set)
    venue: Optional[str] = field(default=None)
    location: Optional[str] = field(default=None)
    url: Optional[str] = field(default=None)
    tg_url: Optional[str] = field(default=None)
    image: Optional[str] = field(default=None)
    category: Category = field(default=Category.GENERAL)
    cancelled: bool = field(default=False)

    def __hash__(self) -> int:
        return hash((self.title, self.date, self.time))

    def get_hash(self) -> int:
        return self.__hash__()

    def has_poster(self) -> bool:
        return bool(self.image)

    def get_weekdays(self) -> str:
        result = ""
        if len(self.days) == 1:
            return weekday.name[next(iter(self.days)).value]
        value = sum([2**day.value for day in self.days])
        if value in weekday.name.keys():
            return weekday.name[value]

        previous_sequence = False
        current_sequence = False
        long_sequence = False
        for day in range(7):
            if Day(day) in self.days:
                if current_sequence:
                    long_sequence = True
                else:
                    current_sequence = True
                    if previous_sequence:
                        result += ","
                    result += weekday.name[day]
            else:
                if current_sequence:
                    if long_sequence:
                        result += f"-{weekday.name[day - 1]}"
                    previous_sequence = True
                    current_sequence = False
                    long_sequence = False
        return result

    def get_title(self) -> Optional[str]:
        if not self.title:
            return None
        if not self.emoji:
            return self.title
        return f"{self.emoji} {self.title}"

    def get_title_repr(self) -> Optional[str]:
        if not self.title:
            return None
        if self.tg_url:
            title = f"[{self.title}]({self.tg_url})"
        elif self.url:
            title = f"[{self.title}]({self.url})"
        else:
            title = self.title
        if not self.emoji:
            return title
        return f"{self.emoji} {title}"

    def get_current_repr(self) -> Optional[str]:
        if not self.title:
            return None
        result = ""
        if self.occurrence != Occurrence.REGULAR:
            if self.date:
                if self.date < Calendar.get_this_week():
                    result = f"`🗓️до`"
                else:
                    result = f"`🗓️{weekday.name[self.date.weekday()]}`"
            if self.end_date and self.end_date > self.date:
                if self.date < Calendar.get_this_week():
                    if self.end_date < Calendar.get_next_week():
                        result += f" `{weekday.name[6]}`"
                    else:
                        result += f' `{self.end_date.strftime("%m/%d")}`'
                elif self.end_date >= Calendar.get_next_week():
                    result += f' до `{self.end_date.strftime("%m/%d")}`'
                else:
                    result += f"`-{weekday.name[self.end_date.weekday()]}`"
        else:
            result = f"`🗓️{self.get_weekdays()}`"
        if self.time:
            result += f" `{clock.emoji(self.time)}"
            if self.time.minute == 0:
                result += f'{self.time.strftime("%H")}`'
            else:
                result += f'{self.time.strftime("%H:%M")}`'
        if self.date or self.time:
            result += "`:`"
        result += f"{self.get_title_repr()}"
        return result

    def get_future_repr(self) -> Optional[str]:
        if not self.title or self.occurrence == Occurrence.REGULAR:
            return None
        result = ""
        if self.date:
            result = f'`🗓️{self.date.strftime("%m/%d")}`'
            if self.end_date and self.end_date > self.date:
                if self.date.month != self.end_date.month:
                    result += f'`-{self.end_date.strftime("%m/%d")}`'
                else:
                    result += f'`-{self.end_date.strftime("%d")}`'
            result += "`:`"
        result += f"{self.get_title_repr()}"
        return result

    def get_full_repr(self) -> Optional[str]:
        if not self.title:
            return None
        result = "*"
        if self.emoji:
            result += f"{self.emoji} "
        result += f"{self.title}*\n\n"
        if self.description:
            result += f"{self.description}\n\n"
        date_or_days = False
        if self.occurrence != Occurrence.REGULAR:
            if self.date:
                date_or_days = True
                result += f'`🗓️{self.date.strftime("%m/%d")}`'
                if self.end_date and self.end_date > self.date:
                    if self.date.month != self.end_date.month:
                        result += f'`-{self.end_date.strftime("%m/%d")}`'
                    else:
                        result += f'`-{self.end_date.strftime("%d")}`'
        elif len(self.days) > 0:
            date_or_days = True
            result += f"`🗓️{self.get_weekdays()}`"
        if self.time:
            if date_or_days:
                result += " "
            result += f'`{clock.emoji(self.time)}{self.time.strftime("%H:%M")}`'
        if date_or_days or self.time:
            result += "\n"
        if self.location:
            if self.venue:
                result += f"📍[{self.venue}]({self.location})\n\n"
            else:
                result += f"📍[Location]({self.location})\n\n"
        elif self.venue:
            result += f"📍{self.venue}\n\n"
        else:
            result += "\n"
        if self.url:
            result += f"🔗 [{link.provider(self.url)}]({self.url})\n\n"
        result += "_#events_"
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result

    def post(self) -> Dict[str, str]:
        result = {"text": self.get_full_repr()}
        if self.image:
            result = {"photo": self.image, "caption": self.get_full_repr()}
        return result

    def to_dict(self, recursive: bool = False) -> dict:
        return {
            "title": self.title,
            "emoji": self.emoji,
            "description": self.description,
            "occurrence": self.occurrence.name if self.occurrence else None,
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.isoformat() if self.time else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "days": [day.name for day in self.days],
            "venue": self.venue,
            "location": self.location,
            "url": self.url,
            "tg_url": self.tg_url,
            "image": self.image,
            "category": self.category.name,
            "cancelled": self.cancelled,
        }


class Calendar:
    def __init__(self):
        self.__events: Dict[int, Event] = {}
        self.__next_id: int = 0

    def add_event(self, event: Event) -> int:
        event_id = self.__next_id
        self.__events[event_id] = event
        self.__next_id += 1
        return event_id

    def delete_event(self, event: Event) -> bool:
        for event_id, calendar_event in self.__events.items():
            if calendar_event == event:
                del self.__events[event_id]
                return True
        return False

    def get_event(self, event_id: int) -> Optional[Event]:
        return self.__events.get(event_id)

    def get_nearest_events(self) -> List[Event]:
        result = []
        this_week = Calendar.get_this_week()
        next_week = Calendar.get_next_week()
        for _, event in self.__events.items():
            if (
                not event.date
                or this_week <= event.date < next_week
                or (event.end_date and event.date < this_week <= event.end_date)
            ):
                result.append(event)
        return result

    def get_future_events(self) -> List[Event]:
        result = []
        next_week = Calendar.get_next_week()
        for _, event in self.__events.items():
            if event.date and next_week <= event.date:
                result.append(event)
        return result

    def get_simple_agenda(
        self, events: List[Event], category: Category = Category.GENERAL
    ) -> str:
        return "\n".join(
            [event.get_title_repr() for event in events if event.category == category]
        )

    def get_nearest_agenda(
        self, events: List[Event], category: Category = Category.GENERAL
    ) -> str:
        return "\n".join(
            [event.get_current_repr() for event in events if event.category == category]
        )

    def get_future_agenda(
        self, events: List[Event], category: Category = Category.GENERAL
    ) -> str:
        return "\n".join(
            [event.get_future_repr() for event in events if event.category == category]
        )

    def get_agenda(self) -> str:
        result = f"*Порядок тижневий*\n\n"
        nearest_events = self.get_nearest_events()
        events_repr = self.get_nearest_agenda(nearest_events)
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

    def remove_past_events(self) -> bool:
        this_week = Calendar.get_this_week()
        events_to_remove = [
            event_id
            for event_id, event in self.__events.items()
            if event.date
            and event.date < this_week
            and (not event.end_date or event.end_date < this_week)
        ]
        for event_id in events_to_remove:
            del self.__events[event_id]
        return len(events_to_remove) > 0

    def get_this_week() -> date:
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())
        return this_monday

    def get_next_week() -> date:
        next_monday = Calendar.get_this_week() + timedelta(days=7)
        return next_monday

    def __getitem__(self, event_id: int) -> Optional[Event]:
        return self.__events[event_id]

    def __setitem__(self, event_id: int, event: Event):
        self.__events[event_id] = event

    def __delitem__(self, event_id: int):
        del self.__events[event_id]

    def __contains__(self, event_id: int) -> bool:
        return event_id in self.__events

    def __iter__(self):
        return iter(self.__events)

    def items(self):
        return self.__events.items()

    def values(self):
        return self.__events.values()

    def keys(self):
        return self.__events.keys()

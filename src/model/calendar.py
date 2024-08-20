from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Dict, Optional

from format import clock, link


Occurrence = Enum('Occurrence', [
    'WITHIN_DAY',
    'WITHIN_DAYS',
    'REGULAR'
])


@dataclass
class Event:
    title: str
    date: Optional[str] = field(default=None)
    time: Optional[str] = field(default=None)
    end_date: Optional[str] = field(default=None)
    end_time: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    emoji: Optional[str] = field(default=None)
    url: Optional[str] = field(default=None)
    image: Optional[str] = field(default=None)
    type: Optional[str] = field(default=None)
    occurrence: Optional[str] = field(default=None)
    cancelled: bool = field(default=False)

    def __hash__(self) -> int:
        return hash((self.title, self.date, self.time))
    
    def get_hash(self) -> int:
        return self.__hash__()
    
    def has_poster(self) -> bool:
        return bool(self.image)

    def get_title(self) -> Optional[str]:
        if not self.title:
            return None
        result = self.title
        if self.emoji:
            result = self.emoji + result
        return result

    def get_current_repr(self) -> Optional[str]:
        if not self.title:
            return None
        result = self.get_title()
        if self.time:
            result = clock.emoji(self.time) + result
        return result

    def get_future_repr(self) -> Optional[str]:
        if not self.title:
            return None        
        result = self.get_title()
        if self.date:
            result = f'{self.date}: {result}'
        return result

    def get_full_repr(self) -> Optional[str]:
        if not self.title:
            return None
        result = '*'
        if self.emoji:
            result += f'{self.emoji} '
        result += f'{self.title}*\n\n'
        if self.date:
            result += f'🗓️{self.date.strftime("%m/%d")}'
            if self.time:
                result += f' {clock.emoji(self.time)}{self.time.strftime("%H:%M")}'
            result += '\n'
        if self.url:
            result += f'🔗 [{link.provider(self.url)}]({self.url})\n\n'
        result += '_#events_'
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result
    
    def post(self) -> Dict[str, str]:
        result = {'text': self.get_full_repr()}
        if self.image:
            result = {'photo': self.image, 'caption': self.get_full_repr()}
        return result

    def to_dict(self, recursive: bool = False) -> dict:
        return {
            'title': self.title,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.isoformat() if self.time else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'description': self.description,
            'emoji': self.emoji,
            'url': self.url,
            'image': self.image,
            'type': self.type,
            'occurrence': self.occurrence.name if self.occurrence else None,
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


# class Calendar:
#     def __init__(self):
#         self.__new_event_id = 0
#         self.__events = []

#     def append(self, event) -> None:
#         event.id = self.__new_event_id
#         self.__new_event_id += 1
#         self.__events.append(event)

#     def get_event_by_title(self, title):
#         return next((event for event in self.__events if event.title == title), None)
    
#     def __iter__(self):
#         return iter(self.__events)
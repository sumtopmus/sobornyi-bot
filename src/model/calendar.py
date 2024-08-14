from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Optional

from format import clock, link


Occurrence = Enum('Occurrence', [
    'WITHIN_DAY',
    'WITHIN_DAYS',
    'REGULAR'
])


@dataclass
class Event:
    title: str
    id: Optional[int] = field(default=None)
    date: Optional[str] = field(default=None)
    time: Optional[str] = field(default=None)
    end_date: Optional[str] = field(default=None)
    end_time: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    emoji: str = field(default='')
    url: Optional[str] = field(default=None)
    image: Optional[str] = field(default=None)
    type: Optional[str] = field(default=None)
    occurrence: Optional[str] = field(default=None)

    def __hash__(self) -> int:
        return hash((self.title, self.date, self.time))
    
    def get_hash(self) -> int:
        return self.__hash__()

    def get_title(self) -> str:
        return f'{self.emoji}{self.title}'
    
    def get_current_repr(self) -> str:
        return clock.emoji(self.time) + self.get_title()

    def get_future_repr(self) -> str:
        return f'{self.date}: {self.get_title()}'

    def get_full_repr(self) -> str:
        return (
            f'*{self.emoji} {self.title}*\n'
            f'\n'
            f'`🗓️{self.date.strftime("%m/%d")} {clock.emoji(self.time)}{self.time.strftime("%H:%M")}`\n'
            f'🔗 [{link.provider(self.url)}]({self.url})\n'
            f'\n'
            f'_#events_'
        )

    def to_dict(self, recursive: bool = False) -> dict:
        return {
            'id': self.id,
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
        self.__new_event_id = 0
        self.__events = []

    def append(self, event) -> None:
        event.id = self.__new_event_id
        self.__new_event_id += 1
        self.__events.append(event)

    def get_event_by_title(self, title):
        return next((event for event in self.__events if event.title == title), None)
    
    def __iter__(self):
        return iter(self.__events)
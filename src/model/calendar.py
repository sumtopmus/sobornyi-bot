from enum import Enum

from format import clock, link


Occurrence = Enum('Occurrence', [
    'WITHIN_DAY',
    'WITHIN_DAYS',
    'REGULAR'
])


class Event:
    def __init__(self, title):
        self.id = None
        self.title = title
        self.date = None
        self.time = None
        self.end_date = None
        self.end_time = None
        self.description = None
        self.emoji = ''
        self.url = None
        self.image = None
        self.type = None
        self.occurrence = None

    def __hash__(self) -> int:
        return hash((self.title, self.date, self.time))
    
    def __repr__(self) -> str:
        return (f"Event('{self.title}')")
    
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
            f'*{self.emoji}{self.title}*\n'
            f'\n'
            f'`🗓️{self.date.strftime("%m/%d")} {clock.emoji(self.time)}{self.time.strftime("%H:%M")}`\n'
            f'🔗 [{link.provider(self.url)}]({self.url})\n'
            f'\n'
            f'_#events_'
        )


class Calendar:
    def __init__(self):
        self.__new_event_id = 0
        self.__events = []

    def append(self, event) -> None:
        event.id = self.__new_event_id
        self.__new_event_id += 1
        self.__events.append(event)
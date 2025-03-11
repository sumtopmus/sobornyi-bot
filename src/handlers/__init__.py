from .debug import debug
from .debug import error_handler as error
from .debug import handlers as debug_handlers

from . import calendar
from . import channel
from . import request
from . import topic
from . import war
from . import welcome


__all__ = ["all", "debug", "calendar", "error", "war", "welcome"]

# Business logic handlers
logic_handlers = []
modules = [calendar, channel, request, topic, war, welcome]
for module in modules:
    logic_handlers.extend(module.create_handlers())
# All handlers (debug + logic)
all = debug_handlers + logic_handlers

from . import calendar, channel, topic, war, welcome
from .debug import debug
from .debug import error_handler as error
from .debug import handlers as debug_handlers

__all__ = ["all", "debug", "calendar", "error", "war", "welcome"]

# Business logic handlers
logic_handlers = []
modules = [calendar, channel, topic, war, welcome]
for module in modules:
    logic_handlers.extend(module.create_handlers())
# All handlers (debug + logic)
all = debug_handlers + logic_handlers

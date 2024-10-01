from .error import handler as error
from . import debug
from . import info
from . import upload

from . import calendar
from . import channel
from . import request
from . import topic
from . import war
from . import welcome


__all__ = ["all", "calendar", "error", "war", "welcome"]

# Debug handlers
debug_handlers = []
modules = [debug, info, upload]
for module in modules:
    debug_handlers.extend(module.create_handlers())
# Business logic handlers
logic_handlers = []
modules = [calendar, channel, request, topic, war, welcome]
for module in modules:
    logic_handlers.extend(module.create_handlers())
# All handlers (debug + logic)
all = debug_handlers + logic_handlers

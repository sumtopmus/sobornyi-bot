from .error import handler as error
from . import debug
from . import info

from . import calendar
from . import channel
from . import request
from . import topic
from . import war
from . import welcome


# Debug handlers
debug_handlers = []
for module in [debug, info]:
    debug_handlers.extend(module.create_handlers())
# Business logic handlers
logic_handlers = []
for module in [calendar, channel, request, topic, war, welcome]:
    logic_handlers.extend(module.create_handlers())
# All handlers (debug + logic)
all = debug_handlers + logic_handlers

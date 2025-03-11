"""Debug handlers module."""

from .error import handler as error_handler

from . import debug
from . import info
from . import upload

__all__ = ["debug", "error_handler", "handlers"]

# Debug handlers
handlers = []
for module in [debug, info, upload]:
    handlers.extend(module.create_handlers())

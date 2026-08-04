"""Debug handlers module."""

from . import debug, info, upload
from .error import handler as error_handler

__all__ = ["debug", "error_handler", "handlers"]

# Debug handlers
handlers = []
for module in [debug, info, upload]:
    handlers.extend(module.create_handlers())

import logging
import os

import config
import tools


def makedirs() -> None:
    """Creates the directiry tree structure."""
    for path in [config.LOG_PATH]:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))


def init() -> None:
    """Initialization."""
    # Create directory tree structure.
    makedirs()
    # Set up logging and debugging.
    if os.path.exists(config.LOG_PATH):
        os.remove(config.LOG_PATH)
    logging_level = logging.DEBUG if config.DEBUG_MODE else logging.INFO
    logging.basicConfig(filename=config.LOG_PATH, level=logging_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Show admin and chat ids.
    tools.debug(f'admins: {", ".join(config.ADMINS)}')
    tools.debug(f'chat: {config.CHAT_ID}')

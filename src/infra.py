from datetime import datetime
import logging
import os

# Magic values.
FMT = '%Y-%m-%d %H:%M:%S'

# Creates the directiry tree structure.
def makedirs(config):
    for path in [config.LOG_FILE]:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

# Debugging helper.
def debug(message, update=None, context=None):
    logging.getLogger(__name__).debug(message)
    if DEBUG_MODE:
        message = f'⌚️ {datetime.now().strftime(FMT)}: {message}'
        if update and context:
            context.bot.sendMessage(chat_id=update.message.chat.id,
                                    text=f'```{message}```')
        print(message)

# Mention a user.
def mention(user):
    result = f'[{user.name}]'
    if user.username:
        result += f'(mention:{user.name})'
    else:
        result += f'(tg://user?id={user.id})'
    return result

# Inialization.
def init(config, debug_mode):
    global DEBUG_MODE
    DEBUG_MODE = debug_mode
    # Create directory tree structure.
    makedirs(config)
    # Set up logging and debugging.
    if os.path.exists(config.LOG_FILE):
        os.remove(config.LOG_FILE)
    logging_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    logging.basicConfig(filename=config.LOG_FILE, level=logging_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Show admin and chat ids.
    debug(f'admin: {config.ADMIN_ID}')
    debug(f'chat: {config.CHAT_ID}')

if __name__ == '__main__':
    init()
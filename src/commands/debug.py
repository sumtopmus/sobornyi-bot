import infra

# Switch between dev and prod modes.
def debug_switch(update, context):
    infra.debug('debug_switch', update, context)
    infra.DEBUG_MODE = not infra.DEBUG_MODE

# Switch to the dev mode.
def debug_on(update, context):
    infra.debug('debug_on', update, context)
    infra.DEBUG_MODE = True

# Switch to the prod mode.
def debug_off(update, context):
    infra.debug('debug_off', update, context)
    infra.DEBUG_MODE = False

# updater.dispatcher.add_handler(CommandHandler('debug', debug_switch,
#     Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))
# updater.dispatcher.add_handler(CommandHandler('debug_on', debug_on,
#     Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))
# updater.dispatcher.add_handler(CommandHandler('debug_off', debug_off,
#     Filters.user(ADMIN_ID) & Filters.chat(CHAT_ID)))

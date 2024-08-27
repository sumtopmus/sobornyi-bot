from dynaconf import settings
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext


from model.calendar import Day, Occurrence
from utils import log


State = Enum('State', [
    # Menu state:
    'CALENDAR_MENU',
    'EVENT_MENU',
    'DATETIME_MENU',
    'BACK',
    'EXIT',
    # Prefix states:
    'EVENT',
    'CATEGORY',
    'OCCURRENCE',
    'WEEKDAY',
    # Process states:
    'CALENDAR_CLEANUP',
    'AGENDA_PREVIEW',
    'AGENDA_EDITING_IMAGE',
    'AGENDA_PUBLISHING',
    'EVENT_ADDING',
    'EVENT_EDITING',
    'EVENT_PICKING',
    'EVENT_NOT_FOUND',
    'EVENT_PREVIEW',
    'EVENT_PUBLISHING',
    'EVENT_DELETING',
    'EVENT_DELETING_CONFIRMATION',
    'EVENT_FINDING',
    'EVENT_WAITING_FOR_TITLE',
    'EVENT_EDITING_TITLE',
    'EVENT_EDITING_EMOJI',
    'EVENT_EDITING_DESCRIPTION',
    'EVENT_EDITING_CATEGORY',
    'EVENT_EDITING_OCCURRENCE',
    'EVENT_EDITING_DATETIME',
    'EVENT_EDITING_DATE',
    'EVENT_EDITING_END_DATE',
    'EVENT_EDITING_TIME',
    'EVENT_EDITING_END_TIME',
    'EVENT_EDITING_DATE_END',
    'EVENT_EDITING_VENUE',
    'EVENT_EDITING_LOCATION',
    'EVENT_EDITING_URL',
    'EVENT_EDITING_IMAGE',
])


async def update_menu(update: Update, menu: dict, new_message: bool = False):
    if new_message or not update.callback_query:
        await update.effective_user.send_message(**menu)
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(**menu)


async def calendar_menu(update: Update, context: CallbackContext, prefix_text: str = None, new_message: bool = False) -> State:
    log('calendar_menu')
    text = 'Ви знаходитесь в меню редагування календаря. Що Ви хочете зробити?'
    if prefix_text:
        text = prefix_text + '\n\n' + text
    image = context.bot_data['agenda']['image']
    keyboard = [
        [
            InlineKeyboardButton('➕ Add', callback_data=State.EVENT_ADDING.name),
            InlineKeyboardButton('📝 Edit', callback_data=State.EVENT_EDITING.name),
        ],
        [
            InlineKeyboardButton('🖼️ Poster ' + ('✅' if image else '🚫'), callback_data=State.AGENDA_EDITING_IMAGE.name),
            InlineKeyboardButton('👓 Preview', callback_data=State.AGENDA_PREVIEW.name),
        ],        
        [
            InlineKeyboardButton('🔄 Update', callback_data=State.CALENDAR_CLEANUP.name),
            InlineKeyboardButton('« Exit', callback_data=State.EXIT.name),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    menu = {'text': text, 'reply_markup': reply_markup}
    await update_menu(update, menu, new_message)
    context.user_data['current_event'] = None
    context.user_data['state'] = State.CALENDAR_MENU
    return State.CALENDAR_MENU


def events_menu(events: dict, add_search_button: bool = True) -> dict:
    sorted_events = sorted(events, key=lambda item: (item[1].date is None, item[1].date))
    ids_and_titles = [(id, event.get_title()) for id, event in sorted_events]
    back_button = InlineKeyboardButton('🔙', callback_data=State.CALENDAR_MENU.name)
    if len(ids_and_titles) == 0:
        text = 'Жодних подій не знайдено.'
        reply_markup = InlineKeyboardMarkup([[back_button]])
        return {'text': text, 'reply_markup': reply_markup}
    text = 'Будь ласка, оберіть захід, який Ви хочете відредагувати.'
    keyboard = []
    for index, (id, title) in enumerate(ids_and_titles):
        keyboard.append([InlineKeyboardButton(title, callback_data=f'{State.EVENT.name}:{id}')])
        if index == 4:
            break
    last_row = []
    if add_search_button:
        last_row.append(InlineKeyboardButton('🔍 Search', callback_data=State.EVENT_FINDING.name))
    last_row.append(back_button)
    keyboard.append(last_row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'text': text, 'reply_markup': reply_markup}


async def event_menu(update: Update, context: CallbackContext, prefix_text: str = None, new_message: bool = False) -> State:
    log('event_menu')
    event = context.user_data['current_event']
    datetime_value = event.time and (event.date or len(event.days) > 0)
    buttons = [
        ('Емоджи', event.emoji, State.EVENT_EDITING_EMOJI),
        ('Назва', event.title, State.EVENT_EDITING_TITLE),
        ('Опис', event.description, State.EVENT_EDITING_DESCRIPTION),
        ('Категорія', event.category, State.EVENT_EDITING_CATEGORY),
        ('Формат', event.occurrence, State.EVENT_EDITING_OCCURRENCE),
        ('Дата і час', datetime_value, State.EVENT_EDITING_DATETIME),
        ('Локація', event.venue, State.EVENT_EDITING_VENUE),
        ('Мапа', event.location, State.EVENT_EDITING_LOCATION),
        ('Посилання', event.url, State.EVENT_EDITING_URL),
        ('Постер', event.image, State.EVENT_EDITING_IMAGE),
    ]
    keyboard, row = [], []
    for text, value, state in buttons:
        row.append(InlineKeyboardButton(text + (' ✅' if value else ' 🚫'), callback_data=state.name))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    keyboard.extend([
        [
            InlineKeyboardButton('👓 Preview', callback_data=State.EVENT_PREVIEW.name),
            InlineKeyboardButton('📺 Publish', callback_data=State.EVENT_PUBLISHING.name),
        ],
        [
            InlineKeyboardButton('❌ Delete', callback_data=State.EVENT_DELETING.name),
            InlineKeyboardButton('🔙', callback_data=State.CALENDAR_MENU.name),
        ]
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = event.get_full_repr()
    if prefix_text:
        if new_message:
            text = prefix_text
        else:
            text = prefix_text + '\n\n' + text
    menu = {'text': text, 'reply_markup': reply_markup}
    await update_menu(update, menu, new_message)
    context.user_data['state'] = State.EVENT_MENU
    return State.EVENT_MENU


async def datetime_menu(update: Update, context: CallbackContext, prefix_text: str = None, new_message: bool = False) -> State:
    log('datetime_menu')
    event = context.user_data['current_event']
    buttons = [
        ('Час (початок)', event.time, State.EVENT_EDITING_TIME),
        ('Час (кінець)', event.end_time, State.EVENT_EDITING_END_TIME),
    ]
    time_row = []
    for text, value, state in buttons:
        time_row.append(InlineKeyboardButton(text + (' ✅' if value else ' 🚫'), callback_data=state.name))
    if event.occurrence == Occurrence.REGULAR:
        buttons = [
            ('Пн', 0, {Day.Monday}),
            ('Вт', 1, {Day.Tuesday}),
            ('Ср', 2, {Day.Wednesday}),
            ('Чт', 3, {Day.Thursday}),
            ('Пт', 4, {Day.Friday}),
            ('Будні', 31, {Day.Monday, Day.Tuesday, Day.Wednesday, Day.Thursday, Day.Friday}),
            ('Сб', 5, {Day.Saturday}),
            ('Нд', 6, {Day.Sunday}),
            ('Вихідні', 96, {Day.Saturday, Day.Sunday}),
        ]
        keyboard, row = [], []
        for text, value, days in buttons:
            row.append(InlineKeyboardButton(text + (' ✅' if days.issubset(event.days) else ' 🚫'), callback_data=f'{State.WEEKDAY.name}:{value}'))
            if len(row) == 3:
                keyboard.append(row)
                row = []
    else:
        buttons = [
            ('Дата (початок)', event.date, State.EVENT_EDITING_DATE),
            ('Дата (кінець)', event.end_date, State.EVENT_EDITING_END_DATE),
        ]
        date_row = []
        for text, value, state in buttons:
            date_row.append(InlineKeyboardButton(text + (' ✅' if value else ' 🚫'), callback_data=state.name))
        keyboard = [date_row]
    keyboard.append(time_row)
    keyboard.append([InlineKeyboardButton('🔙', callback_data=State.EVENT_MENU.name)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = event.get_full_repr()
    if prefix_text:
        if new_message:
            text = prefix_text
        else:
            text = prefix_text + '\n\n' + text
    menu = {'text': text, 'reply_markup': reply_markup}
    await update_menu(update, menu, new_message)
    context.user_data['state'] = State.DATETIME_MENU
    return State.DATETIME_MENU


def construct_back_button(state: State = State.BACK) -> dict:
    keyboard = [[InlineKeyboardButton('🔙', callback_data=state.name)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'reply_markup': reply_markup}

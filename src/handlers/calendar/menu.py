from dynaconf import settings
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ContextTypes


from utils import log


State = Enum('State', [
    # Menu state:
    'CALENDAR_MENU',
    'EVENT_MENU',
    'BACK',
    'EXIT',
    # Prefix states:
    'EVENT',
    # Process states:
    'EVENT_ADDING',
    'EVENT_EDITING',
    'EVENT_PICKING',
    'EVENT_DELETING',
    'EVENT_DELETING_CONFIRMATION',
    'EVENT_FINDING',
    'EVENT_WAITING_FOR_TITLE',
    'EVENT_EDITING_TITLE',
    'EVENT_EDITING_EMOJI',
    'EVENT_EDITING_DESCRIPTION',
    'EVENT_EDITING_OCCURRENCE',
    'EVENT_EDITING_DATE',
    'EVENT_EDITING_TIME',
    'EVENT_EDITING_DATE_END',
    'EVENT_EDITING_URL',
    'EVENT_EDITING_IMAGE',
])


async def update_menu(update: Update, menu: dict):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(**menu)
    else:
        await update.effective_user.send_message(**menu)


async def calendar_menu(update: Update, context: CallbackContext, prefix_text: str = None) -> State:
    log('calendar_menu')
    text = 'Ви знаходитесь в меню редагування календаря. Що Ви хочете зробити?'
    if prefix_text:
        text = prefix_text + '\n\n' + text
    keyboard = [
        [
            InlineKeyboardButton("Додати подію", callback_data=State.EVENT_ADDING.name),
            InlineKeyboardButton("Редагувати подію", callback_data=State.EVENT_EDITING.name),
        ],
        [
            InlineKeyboardButton("« Вийти", callback_data=State.EXIT.name),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)    
    menu = {'text': text, 'reply_markup': reply_markup}
    await update_menu(update, menu)
    context.user_data['state'] = State.CALENDAR_MENU
    return State.CALENDAR_MENU


def events_menu(events: dict, add_search_button: bool = True) -> dict:
    log(events)
    sorted_events = sorted(events, key=lambda item: (item[1].date is None, item[1].date))
    ids_and_titles = [(id, event.title) for id, event in sorted_events]
    back_button = InlineKeyboardButton('« Назад', callback_data=State.CALENDAR_MENU.name)
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
        last_row.append(InlineKeyboardButton('🔍 Пошук', callback_data=State.EVENT_FINDING.name))
    last_row.append(back_button)
    keyboard.append(last_row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'text': text, 'reply_markup': reply_markup}


async def event_menu(update: Update, context: CallbackContext, prefix_text: str = None) -> State:
    log('event_menu')
    event = context.bot_data['current_event']
    text = event.get_full_repr()
    if prefix_text:
        text = prefix_text + '\n\n' + text
    keyboard = [
        [
            InlineKeyboardButton('Емоджи', callback_data=State.EVENT_EDITING_EMOJI.name),
            InlineKeyboardButton('Назва', callback_data=State.EVENT_EDITING_TITLE.name),
        ],
        [
            InlineKeyboardButton('Опис', callback_data=State.EVENT_EDITING_DESCRIPTION.name),
            InlineKeyboardButton('Формат', callback_data=State.EVENT_EDITING_OCCURRENCE.name),
        ],
        [
            InlineKeyboardButton('Дата', callback_data=State.EVENT_EDITING_DATE.name),
            InlineKeyboardButton('Час', callback_data=State.EVENT_EDITING_TIME.name),
        ],
        [
            InlineKeyboardButton('Посилання', callback_data=State.EVENT_EDITING_URL.name),
            InlineKeyboardButton('Постер', callback_data=State.EVENT_EDITING_IMAGE.name),
        ],
        [
            # InlineKeyboardButton("Зберегти 💾", callback_data=State.EVENT_SAVING.name),
            InlineKeyboardButton("Видалити ❌", callback_data=State.EVENT_DELETING.name),  
            InlineKeyboardButton("« Назад", callback_data=State.CALENDAR_MENU.name),          
        ],
    ]        
    reply_markup = InlineKeyboardMarkup(keyboard)
    menu = {'text': text, 'reply_markup': reply_markup}
    await update_menu(update, menu)
    context.user_data['state'] = State.EVENT_MENU
    return State.EVENT_MENU


def construct_back_button(state: State = State.BACK) -> dict:
    log('construct_back_button')
    keyboard = [[InlineKeyboardButton('« Назад', callback_data=state.name)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return {'reply_markup': reply_markup}

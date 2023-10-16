from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# inline клавиатура со ссылками на просмотр фильма/сериала
def create_links_keyboard(names: list[str], links: list[str]) -> InlineKeyboardMarkup:
    """
    Create keyboard with inline buttons: name -> url
    :param names: names of websites
    :param links: urls to websites
    :return: keyboard with links
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i in range(len(names)):
        keyboard.insert(InlineKeyboardButton(text=names[i], url=links[i]))

    return keyboard


# inline клавиатура со вспомогательными командами
stats_button_inline = InlineKeyboardButton(text='Моя статистика 📈', callback_data="/stats")
history_button_inline = InlineKeyboardButton(text='История поиска 📖', callback_data="/history")
heap_button_inline = InlineKeyboardButton(text='Помощь 🌟', callback_data="/help")

additional_keyboard = InlineKeyboardMarkup(row_width=1)
additional_keyboard.insert(stats_button_inline)
additional_keyboard.insert(history_button_inline)
additional_keyboard.insert(heap_button_inline)

from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


async def inline_ls(ls):
    keyboard = InlineKeyboardBuilder()
    if ls:
        for l in ls:
            keyboard.add(InlineKeyboardButton(text=f'🏠 {str(l.ls)}-{str(l.kv)}', callback_data=f'show_ls:{str(l.ls)}'))
    keyboard.add(InlineKeyboardButton(text=f'🔍 Добавить лицевой счет', callback_data='add_ls'))
    return keyboard.adjust(1).as_markup()


async def inline_show_ipu(ls: int, ipu):
    keyword = InlineKeyboardBuilder()
    type_mapping = {
        'hv': 'ХВС',
        'gv': 'ГВС',
        'e': 'ЭЛ-ВО'
    }
    if ipu:
        for i in ipu:
            # Получаем текст из кортежа по типу
            display_type = type_mapping.get(i.type, i.type)  # Если тип не найден, используем оригинальный
            number_display = i.number if i.number is not None else ' '  # Пустая строка, если None
            location_display = i.location if i.location is not None else ' '  # Пустая строка, если None

            keyword.row(InlineKeyboardButton(text=f"{display_type}, {number_display} {location_display}",
                                             callback_data=f'add_pokazaniya:{i.ls}:{i.type}'))

    keyword.row(InlineKeyboardButton(text=f'⬅️ Возврат в начало', callback_data='all_ls_call'),
                InlineKeyboardButton(text=f'❌ Отвязать счет', callback_data=f'del_ls:{ls}'))
    return keyword.as_markup()


async def inline_del_ls(ls: int):
    keyword = InlineKeyboardBuilder()
    keyword.row(InlineKeyboardButton(text=f'Да', callback_data=f'del_ls_yes:{ls}'),
                InlineKeyboardButton(text=f'Нет', callback_data=f'all_ls_call'))
    return keyword.as_markup()


async def inline_back(ls: int):
    keyword = InlineKeyboardBuilder()
    keyword.row(InlineKeyboardButton(text=f'⬅️ Возврат к списку счетчиков', callback_data=f'show_ls:{ls}'))
    return keyword.as_markup()

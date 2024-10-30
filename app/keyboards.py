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

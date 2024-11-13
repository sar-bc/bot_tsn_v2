from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from datetime import date


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


# Admin keyboars

async def inline_menu_admin():
    keyword = InlineKeyboardBuilder()
    keyword.row(
        InlineKeyboardButton(text=f"Импорт л.сч. 🗂", callback_data='import_users'),
        InlineKeyboardButton(text=f"Экспорт л.сч. ♻️", callback_data='export_users')
    )
    # keyword.row(InlineKeyboardButton(text=f"Экспорт лицевых счетов ♻️", callback_data='export_users'))
    keyword.row(
        InlineKeyboardButton(text=f"Импорт ИПУ  🗃", callback_data='import_ipu'),
        InlineKeyboardButton(text=f"Экспорт ИПУ  🗃", callback_data='export_ipu')
    )

    keyword.row(InlineKeyboardButton(text=f"Импорт показаний 📃", callback_data='import_pokazaniya'),
                InlineKeyboardButton(text=f"Экспорт показаний 📘", callback_data='export_pokazaniya'))
    # keyword.row(InlineKeyboardButton(text=f"Экспорт показаний 📘", callback_data='export_pokazaniya'))
    keyword.row(InlineKeyboardButton(text=f"Отправить сообщение пользователям ✍️", callback_data='send_message'))
    return keyword.as_markup()


homes = ['7', '9', '11']


async def reply_choice_home():
    # Создаем клавиатуру
    keyboard = ReplyKeyboardBuilder()

    for home in homes:
        keyboard.add(KeyboardButton(text=home))  # Добавляем кнопку с текстом

    return keyboard.adjust(3).as_markup(resize_keyboard=True)  # Настраиваем количество кнопок в строке


# Функция для создания клавиатуры выбора месяца
async def month_keyboard():
    """Создает клавиатуру для выбора месяца."""
    months = ["Январь", "Февраль", "Март", "Апрель",
              "Май", "Июнь", "Июль", "Август",
              "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
              ]
    keyboard = ReplyKeyboardBuilder()

    for month in months:
        keyboard.add(KeyboardButton(text=month))  # Добавляем кнопку с текстом

    return keyboard.adjust(4).as_markup(resize_keyboard=True)  # Настраиваем количество кнопок в строке


# Функция для создания инлайн-клавиатуры выбора года
async def year_keyboard():
    """Создает инлайн-клавиатуру для выбора года."""
    keyboard = ReplyKeyboardBuilder()

    # Получаем текущий год
    current_year = date.today().year
    for year in range(current_year - 1, current_year + 1):  # Создаем диапазон лет
        keyboard.add(KeyboardButton(text=str(year)))

    return keyboard.adjust(2).as_markup(resize_keyboard=True)  # Настраиваем количество кнопок в строке

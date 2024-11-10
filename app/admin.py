import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import types
import app.keyboards as kb
import logging
from app.states import ImportUsers, ImportIpu, ImportPokazaniya
from database.Database import DataBase
import csv
from pathlib import Path

type_mapping = {
    'hv': 'ХВС',
    'gv': 'ГВС',
    'e': 'ЭЛ-ВО'
}

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

admin = Router()


@admin.message(F.text.lower() == 'admin')
async def admin_command(message: Message, state: FSMContext):
    await state.clear()
    # Получаем Telegram ID пользователя
    telegram_id = message.from_user.id
    db = DataBase()
    admin_tg = await db.check_admin(telegram_id)
    user_state = await db.get_state(message.from_user.id)
    await db.delete_messages(user_state)
    if admin_tg.id_tg == telegram_id:
        sent_mess = await message.answer("Добро пожаловать в админ-меню!", reply_markup=await kb.inline_menu_admin())
        user_state.last_message_ids.append(sent_mess.message_id)
        await db.update_state(user_state)
    else:
        return


# ====================================================================
# Импорт User
@admin.callback_query(F.data.startswith('import_users'))
async def import_users(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.message.answer(f"Прикрепите файл User формата csv\n"
                                  f"Содержимое файла должно быть в таком формате:\n"
                                  f"ls;home;kv;address;flag\n"
                                  f"Кодировка файла utf-8")
    await state.set_state(ImportUsers.input_file)


# обработка файла
@admin.message(ImportUsers.input_file)
async def process_import_users(message: Message, state: FSMContext):
    from main import bot
    document = message.document
    file_id = document.file_id

    # Скачиваем файл
    file = await bot.get_file(file_id)
    file_name = document.file_name  # Получаем имя файла
    file_path = os.path.join("uploaded_files", file_name)  # Путь к сохранению

    # Создаем директорию, если её нет
    os.makedirs("uploaded_files", exist_ok=True)

    # Сохраняем файл на сервере
    await bot.download_file(file.file_path, file_path)
    logger.info(f"file:{file_path}")
    if check_file_extension(file_name, "{'.csv'}"):
        await message.answer("Файл успешно загружен! Ожидайте обработки...")
        if await add_user_from_csv(file_path):
            await message.answer("✅ Файл успешно импортирован")
            delete_file(file_path)
            await admin_command(message, state)
    else:
        logger.error("Ошибка формата файла. Не CSV!")
        await message.answer("❌ Ошибка формата файла! Попробуйте еще раз...")
        await message.answer(f"Прикрепите файл User формата csv\n"
                             f"Содержимое файла должно быть в таком формате:\n"
                             f"ls;home;kv;address;flag\n"
                             f"Кодировка файла utf-8")
        delete_file(file_path)


# ====================================================================
# Импорт ИПУ

@admin.callback_query(F.data.startswith('import_ipu'))
async def import_ipu(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.message.answer(f"Прикрепите файл ИПУ формата csv\n"
                                  f"Содержимое файла должно быть в таком формате:\n"
                                  f"ls;name;number;data_pov_next;location;type\n"
                                  f"Кодировка файла utf-8")
    await state.set_state(ImportIpu.input_file)


# обработка файла
@admin.message(ImportIpu.input_file)
async def process_import_ipu(message: Message, state: FSMContext):
    from main import bot
    document = message.document
    file_id = document.file_id

    # Скачиваем файл
    file = await bot.get_file(file_id)
    file_name = document.file_name  # Получаем имя файла
    file_path = os.path.join("uploaded_files", file_name)  # Путь к сохранению

    # Создаем директорию, если её нет
    os.makedirs("uploaded_files", exist_ok=True)

    # Сохраняем файл на сервере
    await bot.download_file(file.file_path, file_path)
    logger.info(f"file:{file_path}")
    if check_file_extension(file_name, "{'.csv'}"):
        await message.answer("Файл успешно загружен! Ожидайте обработки...")
        if await add_ipu_from_csv(file_path):
            await message.answer("✅ Файл успешно импортирован")
            delete_file(file_path)
            await admin_command(message, state)
    else:
        logger.error("Ошибка формата файла. Не CSV!")
        await message.answer("❌ Ошибка формата файла! Попробуйте еще раз...")
        await message.answer(f"Прикрепите файл ИПУ формата csv\n"
                             f"Содержимое файла должно быть в таком формате:\n"
                             f"ls;name;number;data_pov_next;location;type\n"
                             f"Кодировка файла utf-8")
        delete_file(file_path)


# ====================================================================
# Импорт Показаний

@admin.callback_query(F.data.startswith('import_pokazaniya'))
async def import_pokazaniya(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.message.answer(f"Прикрепите файл Показаний формата csv\n"
                                  f"Содержимое файла должно быть в таком формате:\n"
                                  f"ls;kv;hv;gv;e;date\n"
                                  f"Кодировка файла utf-8")
    await state.set_state(ImportPokazaniya.input_file)


# обработка файла
@admin.message(ImportPokazaniya.input_file)
async def process_import_pokaz(message: Message, state: FSMContext):
    from main import bot
    document = message.document
    file_id = document.file_id

    # Скачиваем файл
    file = await bot.get_file(file_id)
    file_name = document.file_name  # Получаем имя файла
    file_path = os.path.join("uploaded_files", file_name)  # Путь к сохранению

    # Создаем директорию, если её нет
    os.makedirs("uploaded_files", exist_ok=True)

    # Сохраняем файл на сервере
    await bot.download_file(file.file_path, file_path)
    logger.info(f"file:{file_path}")
    if check_file_extension(file_name, "{'.csv'}"):
        await message.answer("Файл успешно загружен! Ожидайте обработки...")
        if await add_pokaz_from_csv(file_path):
            await message.answer("✅ Файл успешно импортирован")
            delete_file(file_path)
            await admin_command(message, state)
    else:
        logger.error("Ошибка формата файла. Не CSV!")
        await message.answer("❌ Ошибка формата файла! Попробуйте еще раз...")
        await message.answer(f"Прикрепите файл Показаний формата csv\n"
                             f"Содержимое файла должно быть в таком формате:\n"
                             f"ls;kv;hv;gv;e;date\n"
                             f"Кодировка файла utf-8")
        delete_file(file_path)


# =============FUNCTIN==================


async def add_user_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        rows = csv.reader(csv_file, delimiter=';')
        headers = next(rows)

        # Проверяем заголовки
        headers_full = ['ls', 'home', 'kv', 'address', 'flag']
        headers_partial = ['ls', 'home', 'kv', 'address']

        if headers != headers_full and headers != headers_partial:
            logger.error("Неверные заголовки файла")
            return False

        db = DataBase()
        for row in rows:
            ls, home, kv, address = row[:4]  # берем 4 элемента
            flag_value = row[4].strip().lower() == '1' if len(row) > 4 else False  # Проверка флага

            if flag_value:
                await db.del_user(ls)
            else:
                await db.add_or_update_user(ls, home, kv, address)

    return True


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

async def add_ipu_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        rows = csv.reader(csv_file, delimiter=';')
        headers = next(rows)

        # Проверяем заголовки
        headers_full = ['ls', 'name', 'number', 'data_pov_next', 'location', 'type', 'flag']
        headers_partial = ['ls', 'name', 'number', 'data_pov_next', 'location', 'type']

        if headers != headers_full and headers != headers_partial:
            logger.error("Неверные заголовки файла")
            return False

        db = DataBase()
        for row in rows:
            ls, name, number, data_pov_next, location, type_ = row[:6]
            flag_value = row[6].strip().lower() == '1' if len(row) > 6 else False  # Проверка флага

            if flag_value:
                await db.del_ipu(ls, type_)
            else:
                await db.add_or_update_ipu(ls, name, number, data_pov_next, location, type_)

    return True


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
async def add_pokaz_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        rows = csv.reader(csv_file, delimiter=';')
        headers = next(rows)

        # Проверяем заголовки
        headers_full = ['ls', 'kv', 'hv', 'gv', 'e', 'date', 'flag']
        headers_partial = ['ls', 'kv', 'hv', 'gv', 'e', 'date']

        if headers != headers_full and headers != headers_partial:
            logger.error("Неверные заголовки файла")
            return False

        db = DataBase()
        for row in rows:
            ls, kv, hv, gv, e, date = row[:6]
            flag_value = row[6].strip().lower() == '1' if len(row) > 6 else False  # Проверка флага

            if flag_value:
                await db.pokaz_admin_del(ls, date)
            else:
                await db.add_or_update_pokaz_admin(ls, kv, hv, gv, e, date)

    return True


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
def check_file_extension(file_name, valid_extensions):
    extension = Path(file_name).suffix  # Получаем расширение файла
    return extension.lower() in valid_extensions  # Проверяем, является ли оно допустимым


# =====================
def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info("Файл успешно удален!")
    else:
        logger.info("Ошибка удаления! Файл не существует.")
# =====================
# =====================
# =====================

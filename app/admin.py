import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import types
import app.keyboards as kb
import logging
from app.states import ImportUsers
from database.Database import DataBase
import csv

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


@admin.callback_query(F.data.startswith('import_users'))
async def import_users(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.message.answer(f"Прикрепите файл формата csv\n"
                                  f"Содержимое файла должно быть в таком формате:\n"
                                  f"ls;home;kv;address\n"
                                  f"123456;7;50;Полный адрес\n"
                                  f"654321;7;55;Полный адрес\n"
                                  f"107497;7;98;Полный адрес\n"
                                  f"\n\n"
                                  f"Кодировка файла utf-8")
    await state.set_state(ImportUsers.input_file)


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
    await message.answer("Файл успешно загружен! Ожидайте обработки...")
    add_data_from_csv(file_path)


def add_data_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        rows = csv.reader(csv_file, delimiter=';')
        if next(rows) != ['ls', 'home', 'kv', 'address']:
            logger.error("Неверные заголовки файла")
            return False

        for row in rows:
            ls, home, kv, address = row
            print(f"ls:{ls};home:{home};kv:{kv};address:{address}")

    return False
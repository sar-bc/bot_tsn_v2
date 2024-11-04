from aiogram import Router
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
import app.keyboards as kb
import logging
from database.Database import DataBase
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
async def admin_command(message: Message):
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

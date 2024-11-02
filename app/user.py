from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from app.middlewares import CounterMiddleware
import app.keyboards as kb
import logging
from aiogram.fsm.context import FSMContext
from app.states import AddLs
from typing import Any, Dict
from database.Database import DataBase

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
user = Router()

user.message.middleware(CounterMiddleware())


@user.message(CommandStart())
async def cmd_start(message: Message):
    logger.info('Команда старт')
    db = DataBase()
    user_state = await db.get_state(message.from_user.id)
    await db.delete_messages(user_state, message)
    await message.answer('Добро пожаловать !')
    await all_ls(user_state, message)


@user.message(AddLs.ls)
async def process_ls(message: Message, state: FSMContext):
    # тут проверка ls на число и на длину
    # если все ок то stste делаем kv
    if 6 <= len(message.text) <= 8:  # длина лицевого
        try:
            await state.update_data(ls=int(message.text))
            await state.set_state(AddLs.kv)
            logger.info('Переходим к вводу квартиры')
            await message.answer("Очень хорошо! Теперь введите номер квартиры (не более 3 символов).")
        except ValueError:
            logger.error('Введеный лицевой не является числом')
            await message.answer("Вы ввели некорректное значение! Введите номер лицевого счета еще раз")
    else:
        logger.error('Неправильная длина лицевого')
        await message.answer("Вы ввели некорректное значение! Введите номер лицевого счета еще раз")


@user.message(AddLs.kv)
async def process_kv(message: Message, state: FSMContext):
    if 1 <= len(message.text) <= 3:
        try:
            data = await state.update_data(kv=int(message.text))
            await state.clear()
            logger.info('Переходим к поиску лицевого')
            await message.answer("Подождите, идёт поиск и привязка лицевого счета..")
            await check_ls(message=message, data=data)
        except ValueError:
            logger.error('Введенная квартира не является числом')
            await message.answer("Вы ввели некорректное значение! Введите номер квартиры еще раз")
    else:
        logger.error('Неправильная длина квартиры')
        await message.answer("Вы ввели некорректное значение! Введите номер квартиры еще раз")


#  # Callback ###
@user.callback_query(F.data == 'add_ls')
async def add_ls(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddLs.ls)
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state, callback.message)
    await callback.answer()
    await callback.message.answer('Введите номер лицевого счета (только цифры, не более 8 цифр).')


@user.callback_query(F.data.startswith('show_ls:'))
async def show_ls(callback: CallbackQuery):
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state, callback.message)
    await callback.answer()
    ls = callback.data.split(':')[1]
    logger.info(f'callback_show_ls:{ls}')
    await callback.message.answer("Получение списка счётчиков... ожидайте.")


#  ####### FUNCTION ###################
async def all_ls(state, message):
    logger.info(f'all_ls:user_id={state.user_id}')
    db = DataBase()
    user_bot = await db.get_userbot(state.user_id)
    sent_mess = await message.answer('Выберите Лицевой счёт из списка, либо добавьте новый',
                                     reply_markup=await kb.inline_ls(user_bot))
    state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(state)


# ############
async def check_ls(message: Message, data: Dict[str, Any]):
    db = DataBase()
    logger.info(f"check_ls:{data['ls']};kv:{data['kv']}")
    u = await db.get_users(data['ls'], data['kv'])
    if u:
        logger.info('такой юзер есть')
        logger.info(u)
        if await db.get_userbot_ls(u.ls):
            await message.answer(f"⛔ Лицевой счет уже добавлен!")
        else:
            # await db.create_userbot(id_tg=message.from_user.id, ls=u.ls, home=u.home, kv=u.kv)
            kwargs = {
                'id_tg': message.from_user.id,
                'ls': u.ls,
                'home': u.home,
                'kv': u.kv
            }
            if await db.create_userbot(**kwargs):
                await message.answer(f"Лицевой счет №{u.ls} успешно добавлен.")
                user_state = await db.get_state(message.from_user.id)
                await all_ls(user_state, message)
            else:
                await message.answer('❌ Не удалось добавить лицевой счет! Обратитесь в офис ТСН')

    else:
        logger.error('такого юзере НЕТ')
        await message.answer('❌ Не удалось найти указанный лицевой счет! Обратитесь в офис ТСН')
        user_state = await db.get_state(message.from_user.id)
        await all_ls(user_state, message)

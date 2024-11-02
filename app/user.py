from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from app.middlewares import CounterMiddleware
import app.keyboards as kb
import logging
from aiogram.fsm.context import FSMContext
from app.states import AddLs, AddPokazaniya
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
    await db.delete_messages(user_state)
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
    await db.delete_messages(user_state)
    await callback.answer()
    await callback.message.answer('Введите номер лицевого счета (только цифры, не более 8 цифр).')


@user.callback_query(F.data.startswith('show_ls:'))
async def show_ls(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.answer()
    ls = int(callback.data.split(':')[1])
    logger.info(f'callback_show_ls:{ls}')
    await callback.message.answer("Получение списка счётчиков... ожидайте.")
    ipu = await db.get_ipu(ls)
    if not ipu:
        await callback.message.answer(f"На лицевом счете №{ls} не найдены приборы учета!")
    users = await db.get_address(ls)
    user_state = await db.get_state(callback.from_user.id)
    sent_mess = await callback.message.answer(f"Лицевой счет № {ls}\n"
                                              f"Адрес: {users.address}\n"
                                              f"Выберите прибор учета из списка",
                                              reply_markup=await kb.inline_show_ipu(ls, ipu))
    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)


@user.callback_query(F.data == 'all_ls_call')
async def all_ls_call(callback: CallbackQuery):
    db = DataBase()
    user_bot = await db.get_userbot(callback.from_user.id)
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    logger.info(f'all_ls_call:user_id={callback.from_user.id}')
    sent_mess = await callback.message.answer(text='Выберите Лицевой счёт из списка, либо добавьте новый',
                                              reply_markup=await kb.inline_ls(user_bot))
    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)


@user.callback_query(F.data.startswith('del_ls:'))
async def del_ls(callback: CallbackQuery):
    ls = int(callback.data.split(':')[1])
    db = DataBase()
    users = await db.get_user_ls(ls)
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    logger.info(f"Поступил запрос на удаление лицевого {ls}")
    sent_mess = await callback.message.answer(f"Вы точно хотите отвязать Лицевой счет?\n"
                                              f"Счет № {ls}\n"
                                              f"Адрес: {users.address}", reply_markup=await kb.inline_del_ls(ls))
    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)


@user.callback_query(F.data.startswith('del_ls_yes:'))
async def del_ls(callback: CallbackQuery):
    ls = int(callback.data.split(':')[1])
    id_tg = callback.from_user.id
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    if await db.del_ls(id_tg, ls):
        await callback.message.answer(f'Лицевой счет №{ls} успешно отвязан!')
    await db.delete_messages(user_state)
    await all_ls(user_state, callback.message)


@user.callback_query(F.data.startswith('add_pokazaniya:'))
async def add_pokazaniya(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    ls = int(callback.data.split(':')[1])
    type_ipu = callback.data.split(':')[2]
    type_mapping = {
        'hv': 'ХВС',
        'gv': 'ГВС',
        'e': 'Электрич.'
    }
    last = await db.get_pokazaniya_last(ls, type_ipu)
    print(last)
    data_display = last.date.strftime("(%d-%m-%Y)") if last is not None else ' '
    previous_value = getattr(last, type_ipu) if last is not None else ' '

    display_type = type_mapping.get(type_ipu, type_ipu)
    previous_display = (
        f"Предыдущее: {previous_value} {data_display}\n"
        if last is not None else ''
    )
    sent_mess = await callback.message.answer(
        f"Прибор учета: {display_type}\n"
        f"{previous_display}"
        f"Введите текущее показание ниже:",
        reply_markup=await kb.inline_back(ls)
    )
    # Использование словаря для сопоставления типов и состояний
    state_mapping = {
        'hv': AddPokazaniya.hv,
        'gv': AddPokazaniya.gv,
        'e': AddPokazaniya.e  # Добавьте другие типы, если необходимо
    }
    # Устанавливаем состояние на основе словаря
    await state.set_state(state_mapping.get(type_ipu, None))  # None, если тип не найден

    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)


@user.message(AddPokazaniya.hv)
async def priem_pokaz(message: Message, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(message.from_user.id)
    await db.delete_messages(user_state)
    logger.info(f"Прием показаний ХВС")
    data = await state.update_data(hv=int(message.text))
    await state.clear()
    await message.answer(f"Введено показание: {data['hv']}... ожидайте")


#  ####### FUNCTION ###################
async def all_ls(state, message):
    logger.info(f'all_ls:user_id={state.user_id}')
    db = DataBase()
    user_bot = await db.get_userbot(state.user_id)
    sent_mess = await message.answer(text='Выберите Лицевой счёт из списка, либо добавьте новый',
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

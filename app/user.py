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
from datetime import date
from app.log import Loger

# Настройка логирования
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
# )
# logger = logging.getLogger(__name__)
logger = Loger()
logger.get_name_log(__name__)

user = Router()

user.message.middleware(CounterMiddleware())

type_mapping = {
    'hv': 'ХВС',
    'gv': 'ГВС',
    'e': 'ЭЛ-ВО'
}


@user.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await logger.info(f'ID_TG:{message.from_user.id}|Команда старт')
    await state.clear()
    db = DataBase()
    user_state = await db.get_state(message.from_user.id)
    await db.delete_messages(user_state)
    await message.answer('Добро пожаловать !')
    await all_ls(user_state, message)


@user.message(AddLs.ls)
async def process_ls(message: Message, state: FSMContext):
    if 6 <= len(message.text) <= 8:  # длина лицевого
        try:
            await state.update_data(ls=int(message.text))
            await state.set_state(AddLs.kv)
            await logger.info(f'ID_TG:{message.from_user.id}|Переходим к вводу квартиры')
            await message.answer("Очень хорошо! Теперь введите номер квартиры (не более 3 символов).")
        except ValueError:
            await logger.error(f'ID_TG:{message.from_user.id}|Введеный лицевой не является числом')
            await message.answer("Вы ввели некорректное значение! Введите номер лицевого счета еще раз")
    else:
        await logger.error(f'ID_TG:{message.from_user.id}|Неправильная длина лицевого')
        await message.answer("Вы ввели некорректное значение! Введите номер лицевого счета еще раз")


@user.message(AddLs.kv)
async def process_kv(message: Message, state: FSMContext):
    if 1 <= len(message.text) <= 3:
        try:
            data = await state.update_data(kv=int(message.text))
            await state.clear()
            await logger.info(f'ID_TG:{message.from_user.id}|Переходим к поиску лицевого')
            await message.answer("Подождите, идёт поиск и привязка лицевого счета..")
            await check_ls(message=message, data=data)
        except ValueError:
            await logger.error(f'ID_TG:{message.from_user.id}|Введенная квартира не является числом')
            await message.answer("Вы ввели некорректное значение! Введите номер квартиры еще раз")
    else:
        await logger.error(f'ID_TG:{message.from_user.id}|Неправильная длина квартиры')
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
    await logger.info(f"ID_TG:{callback.from_user.id}|state.get_state()=>{await state.get_state()}")
    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.answer()
    ls = int(callback.data.split(':')[1])
    await logger.info(f'ID_TG:{callback.from_user.id}|callback_show_ls:{ls}')
    await callback.message.answer("Получение списка счётчиков... ожидайте.")
    ipu = await db.get_ipu(ls)
    print(f"ipu:{ipu}")
    # if not ipu:
    #     await callback.message.answer(f"❌ На лицевом счете №{ls} не найдены приборы учета❗️")
    users = await db.get_address(ls)
    user_state = await db.get_state(callback.from_user.id)
    # sent_mess = await callback.message.answer(f"Лицевой счет № {ls}\n"
    #                                           f"Адрес: {users.address}\n"
    #                                           f"Выберите прибор учета из списка" if ipu else "",
    #                                           reply_markup=await kb.inline_show_ipu(ls, ipu))
    sent_mess = await callback.message.answer(
        f"Лицевой счет № {ls}\n"
        f"Адрес: {users.address}\n"
        f"{'Выберите прибор учета из списка' if ipu else '❌ На лицевом счете не найдены приборы учета❗️'}",
        reply_markup=await kb.inline_show_ipu(ls, ipu)
    )
    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)


@user.callback_query(F.data == 'all_ls_call')
async def all_ls_call(callback: CallbackQuery):
    db = DataBase()
    user_bot = await db.get_userbot(callback.from_user.id)
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await logger.info(f'ID_TG:{callback.from_user.id}|all_ls_call:user_id={callback.from_user.id}')
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
    await logger.info(f"ID_TG:{callback.from_user.id}|Поступил запрос на удаление лицевого {ls}")
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
    # Получаем текущую дату
    current_date = date.today()

    db = DataBase()
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    ls = int(callback.data.split(':')[1])
    type_ipu = callback.data.split(':')[2]
    # смотрим последнее показание
    last = await db.get_pokazaniya_last(ls, type_ipu)
    # print(f"last={last}")
    # запрашиваем данные счетчика
    ipu = await db.get_ipu_type(ls, type_ipu)
    # print(f"ipu={ipu}")
    ipu_number = f", {ipu.number} {ipu.location if len(ipu.location)>1 else ''}" if len(ipu.number) > 4 else ''
    await logger.info(f"ID_TG:{callback.from_user.id}|get_pokazaniya_last:{last}")
    previous_value = getattr(last, type_ipu) if last is not None else ' '
    # print(f"previous_value={previous_value}")
    # запрашиваем адрес
    address = await db.get_address(ls)
    # print(f"address={address}")
    display_type = type_mapping.get(type_ipu, type_ipu)
    # запрашиваем предыдущие показания
    # prev_val = await db.get_pokazaniya_field(ls, type_ipu)
    # print(f"prev_val={prev_val}")
    # сдесь запрашиваем предпоследнее показание
    last_pokazaniya = await db.get_pokazaniya_last_prev(int(ls), current_date)
    # prev_val = getattr(last_pokazaniya, type_ipu)
    if last_pokazaniya is not None:
        prev = getattr(last_pokazaniya, type_ipu)
    else:
        prev = None
    prev_val = f"{prev}" if prev is not None else '-'
    # print(f"prev_val={prev_val}")
    # print(f"last_pokazaniya={last_pokazaniya}")

    previous_display = (
        f"Предыдущее: {prev_val} ({last_pokazaniya.date.strftime('%d-%m-%Y')})\n" if (last is not None) and (prev is not None) else ''
    )
    if last is not None:
        display_new =(
            f"Введено: {getattr(last, type_ipu)} (можно изменить)\n" if last.date == current_date else ''
        )
    else:
        display_new = ''    
    mess = (f"Прибор учета: {display_type}{ipu_number}\n"
            f"{previous_display}"
            f"{display_new}"
            f"Введите ниже текущее показание\nВводите показания целым числом:")
    # print(mess)
    sent_mess = await callback.message.answer(mess, reply_markup=await kb.inline_back(ls))

    await state.set_state(AddPokazaniya.input)
    await state.update_data(kv=address.kv)
    await state.update_data(ls=ls)
    await state.update_data(type_ipu=type_ipu)
    await state.update_data(last_input=previous_value)
    if last is not None:
        await state.update_data(last_data=last.date)
    else:
        # Обработка случая, когда last равно None
        await state.update_data(last_data=None)  # Или любое другое значение по умолчанию
    # await state.update_data(last_data=last.date)
    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)


@user.message(AddPokazaniya.input)
async def priem_pokaz(message: Message, state: FSMContext):
    # Получаем текущую дату
    current_date = date.today()
    db = DataBase()
    user_state = await db.get_state(message.from_user.id)
    await db.delete_messages(user_state)
    data = await state.get_data()
    # call = data.get('callback')
    # await state.clear()
    display_type = type_mapping.get(data.get('type_ipu'), data.get('type_ipu'))
    await db.delete_messages(user_state)
    input_cur = message.text
    await logger.info(f"ID_TG:{message.from_user.id}|data:{data}")
    await message.answer(f"Введено показание {display_type}: {input_cur}... ожидайте")
    if input_cur.isdigit() and 1 <= len(input_cur) <= 8:
        await logger.info(
            f"ID_TG:{message.from_user.id}|Проверку прошли число и длина. Ввели показания {display_type}:{input_cur}")

        if data.get('last_input') != ' ':
            await logger.info(f"ID_TG:{message.from_user.id}|У нас есть предыдущее показание, алгоритм проверки дальше")

            if current_date == data.get('last_data'):
                await logger.info("ДАТЫ РАВНЫ")
                # сдесь запрашиваем предпоследнее показание
                last_pokazaniya = await db.get_pokazaniya_last_prev(
                    int(data.get('ls')), data.get('last_data').strftime('%Y-%m-%d'))
                if last_pokazaniya:
                    # Получаем значение по полю, указанному в data.get('type_ipu')
                    type_ipu = data.get('type_ipu')  # Получаем тип IPU
                    value = None

                    if type_ipu == 'hv':
                        value = last_pokazaniya.hv  # Получаем значение поля hv
                    elif type_ipu == 'gv':
                        value = last_pokazaniya.gv  # Получаем значение поля gv
                    elif type_ipu == 'e':
                        value = last_pokazaniya.e  # Получаем значение поля e

                    await logger.info(f"last_pokazaniya: {type_ipu} = {value}")
                    value = value if value is not None else '0'
                    try:
                        if int(input_cur) >= int(value):
                            await logger.info(f"ID_TG:{message.from_user.id}|Значение в норме записываем в бд")
                            await state.clear()
                            # функция добавления или обновления показаний
                            await db.add_or_update_pokazaniya(data.get('ls'), data.get('kv'), data.get('type_ipu'),
                                                              input_cur)
                            sent_mess = await message.answer(f"Показания приняты успешно!",
                                                             reply_markup=await kb.inline_back(
                                                                 data.get('ls')))
                            user_state.last_message_ids.append(sent_mess.message_id)
                            await db.update_state(user_state)
                        else:
                            await logger.info(f"ID_TG:{message.from_user.id}|Ошибка значение меньше чем предыдущее")
                            await message.answer("Введенное значение меньше предыдущего! Попробуйте еще раз:")
                    except ValueError:
                        await logger.error(f"ID_TG:{message.from_user.id}|Ошибка значение - сравниваемые показания ("
                                           f"разные типы)")
                        await message.answer("❌ Ошибка!")
                        await all_ls(user_state, message)

                else:
                    await logger.info("Запись не найдена.")
                    # функция добавления или обновления показаний
                    await db.add_or_update_pokazaniya(data.get('ls'), data.get('kv'), data.get('type_ipu'), input_cur)
                    sent_mess = await message.answer(f"Показания приняты успешно!", reply_markup=await kb.inline_back(
                        data.get('ls')))
                    user_state.last_message_ids.append(sent_mess.message_id)
                    await db.update_state(user_state)

            else:
                await logger.info("ДАТЫ НЕ РАВНЫ")
                try:
                    if int(input_cur) >= int(data.get('last_input')):
                        await logger.info(f"ID_TG:{message.from_user.id}|Значение в норме записываем в бд")
                        await state.clear()
                        # функция добавления или обновления показаний
                        await db.add_or_update_pokazaniya(data.get('ls'), data.get('kv'), data.get('type_ipu'), input_cur)
                        sent_mess = await message.answer(f"Показания приняты успешно!", reply_markup=await kb.inline_back(
                            data.get('ls')))
                        user_state.last_message_ids.append(sent_mess.message_id)
                        await db.update_state(user_state)

                    else:
                        await logger.info(f"ID_TG:{message.from_user.id}|Ошибка значение меньше чем предыдущее")
                        await message.answer("Введенное значение меньше предыдущего! Попробуйте еще раз:")
                except ValueError:
                    await logger.error(f"ID_TG:{message.from_user.id}|Ошибка значение - сравниваемые показания ("
                                       f"разные типы)")
                    await message.answer("❌ Ошибка!")
                    await all_ls(user_state, message)

        else:
            await logger.info(f"ID_TG:{message.from_user.id}|НЕТ предыдущих показаний. Не с чем сравнивать, записываем в бд ")
            await state.clear()
            # функция добавления или обновления показаний
            await db.add_or_update_pokazaniya(data.get('ls'), data.get('kv'), data.get('type_ipu'),
                                              input_cur)
            sent_mess = await message.answer(f"Показания приняты успешно!",
                                             reply_markup=await kb.inline_back(
                                                 data.get('ls')))
            user_state.last_message_ids.append(sent_mess.message_id)
            await db.update_state(user_state)
            # функция добавления или обновления показаний
    else:
        await logger.error(f"ID_TG:{message.from_user.id}|Вы ввели некорректное значение {display_type}!")
        await message.answer("Вы ввели некорректное значение! Попробуйте еще раз:")


# 1. введеное коказание проверяем на число и на длину от 1 до 8
# если ошибка то сообщаем что ввели некорректное значение и попросить заново ввести число
# 2. далее смотрим в базу на предыдущее показание оно должно быть больше либо равно
# если значение меньше то сообщаем что переданное значение не может быть меньше предыдущего и
# просим ввести заново
# Если в базе нет сведений о предыдущем показании значит проверяем только на число и длину от 1 до 8 и записываем в базу

#  ####### FUNCTION ###################
async def all_ls(state, message):
    await logger.info(f'ID_TG:{message.from_user.id}|all_ls:user_id={state.user_id}')
    db = DataBase()
    user_bot = await db.get_userbot(state.user_id)
    sent_mess = await message.answer(text='Выберите Лицевой счёт из списка, либо добавьте новый',
                                     reply_markup=await kb.inline_ls(user_bot))
    state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(state)


# ############
async def check_ls(message: Message, data: Dict[str, Any]):
    db = DataBase()
    await logger.info(f"ID_TG:{message.from_user.id}|check_ls:{data['ls']};kv:{data['kv']}")
    u = await db.get_users(data['ls'], data['kv'])
    if u:
        await logger.info(f'ID_TG:{message.from_user.id}|такой юзер есть:{u}')
        if await db.get_userbot_ls(u.ls, message.from_user.id):
            await message.answer(f"⛔ Лицевой счет уже добавлен!")
            user_state = await db.get_state(message.from_user.id)
            await all_ls(user_state, message)
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
        await logger.error(f'ID_TG:{message.from_user.id}|такого юзере НЕТ')
        await message.answer('❌ Не удалось найти указанный лицевой счет! Обратитесь в офис ТСН')
        user_state = await db.get_state(message.from_user.id)
        await all_ls(user_state, message)

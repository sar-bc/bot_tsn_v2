import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import types
import app.keyboards as kb
import logging
from app.states import ImportUsers, ImportIpu, ImportPokazaniya, ChoiceHomeUser, ExportPokazaniya, SendMess
from database.Database import DataBase
import csv
from pathlib import Path
from app.log import Loger

type_mapping = {
    'hv': 'ХВС',
    'gv': 'ГВС',
    'e': 'ЭЛ-ВО'
}
month_mapping = {
    'Январь': '1',
    'Февраль': '2',
    'Март': '3',
    'Апрель': '4',
    'Май': '5',
    'Июнь': '6',
    'Июль': '7',
    'Август': '8',
    'Сентябрь': '9',
    'Октябрь': '10',
    'Ноябрь': '11',
    'Декабрь': '12'
}

# Настройка логирования
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
# )
# logger = logging.getLogger(__name__)
logger = Loger()
logger.get_name_log(__name__)


admin = Router()


@admin.message(F.text.lower() == 'admin')
async def admin_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    await logger.info(f'ID_TG:{message.from_user.id}|Команда старт ADMIN')
    await handle_admin_command(telegram_id, message, state)  # Передаем необходимые параметры


async def handle_admin_command(telegram_id: int, message: Message, state: FSMContext):
    await state.clear()
    db = DataBase()
    admin_tg = await db.check_admin(telegram_id)
    user_state = await db.get_state(telegram_id)

    # Удаляем старые сообщения, если есть
    await db.delete_messages(user_state)

    if admin_tg and admin_tg.id_tg == telegram_id:
        # await message.answer("Добро пожаловать!")
        sent_mess = await message.answer(text="Добро пожаловать!\nАдмин-меню:", reply_markup=await
        kb.inline_menu_admin())
        user_state.last_message_ids.append(sent_mess.message_id)
        await db.update_state(user_state)
    else:
        # await message.answer("У вас нет прав доступа.")
        return


# ====================================================================
# Импорт User

@admin.callback_query(F.data.startswith('import_users'))
async def import_users(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    await logger.info(f'ID_TG:{callback.from_user.id}|Импорт Users')
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
    await logger.info(f"file:{file_path}")
    if check_file_extension(file_name, "{'.csv'}"):
        await message.answer("Файл успешно загружен! Ожидайте обработки...")
        await logger.info(f'ID_TG:{message.from_user.id}|Файл успешно загружен! Ожидайте обработки...')
        if await add_user_from_csv(file_path):
            await message.answer("✅ Файл успешно импортирован")
            await logger.info(f'ID_TG:{message.from_user.id}|Файл успешно импортирован')
            await delete_file(file_path)
            await admin_command(message, state)
        else:
            await message.answer("❌ Ошибка! Не верные заголовки файла.")
            await delete_file(file_path)
            await admin_command(message, state)
    else:
        await logger.error("Ошибка формата файла. Не CSV!")
        await message.answer("❌ Ошибка формата файла! Попробуйте еще раз...")
        await message.answer(f"Прикрепите файл User формата csv\n"
                             f"Содержимое файла должно быть в таком формате:\n"
                             f"ls;home;kv;address;flag\n"
                             f"Кодировка файла utf-8")
        await delete_file(file_path)


# ====================================================================
# Импорт ИПУ

@admin.callback_query(F.data.startswith('import_ipu'))
async def import_ipu(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    await logger.info(f'ID_TG:{callback.from_user.id}|Импорт ИПУ')
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.message.answer(f"Прикрепите файл ИПУ формата csv\n"
                                  f"Содержимое файла должно быть в таком формате:\n"
                                  f"'Лицевой', 'Наименование ПУ', 'Заводской номер', 'Дата следующей поверки', 'Место установки', 'Тип счетчика'\n"
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
    await logger.info(f"file:{file_path}")
    if check_file_extension(file_name, "{'.csv'}"):
        await message.answer("Файл успешно загружен! Ожидайте обработки...")
        await logger.info(f'ID_TG:{message.from_user.id}|Файл успешно загружен! Ожидайте обработки...')
        if await add_ipu_from_csv(file_path):
            await message.answer("✅ Файл успешно импортирован")
            await logger.info(f'ID_TG:{message.from_user.id}|Файл успешно импортирован')
            await delete_file(file_path)
            await admin_command(message, state)
        else:
            await message.answer("❌ Ошибка! Не верные заголовки файла.")
            await delete_file(file_path)
            await admin_command(message, state)
    else:
        await logger.error("Ошибка формата файла. Не CSV!")
        await message.answer("❌ Ошибка формата файла! Попробуйте еще раз...")
        await message.answer(f"Прикрепите файл ИПУ формата csv\n"
                             f"Содержимое файла должно быть в таком формате:\n"
                             f"'Лицевой', 'Наименование ПУ', 'Заводской номер', 'Дата следующей поверки', 'Место установки' ,'Тип счетчика'\n"
                             f"Кодировка файла utf-8")
        await delete_file(file_path)


# ====================================================================
# Импорт Показаний

@admin.callback_query(F.data.startswith('import_pokazaniya'))
async def import_pokazaniya(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    await logger.info(f'ID_TG:{callback.from_user.id}|Импорт Показаний')
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
    await logger.info(f"file:{file_path}")
    if check_file_extension(file_name, "{'.csv'}"):
        await message.answer("Файл успешно загружен! Ожидайте обработки...")
        await logger.info(f'ID_TG:{message.from_user.id}|Файл успешно загружен! Ожидайте обработки...')
        if await add_pokaz_from_csv(file_path):
            await message.answer("✅ Файл успешно импортирован")
            await logger.info(f'ID_TG:{message.from_user.id}|Файл успешно импортирован')
            await delete_file(file_path)
            await admin_command(message, state)
        else:
            await message.answer("❌ Ошибка! Не верные заголовки файла.")
            await delete_file(file_path)
            await admin_command(message, state)
    else:
        await logger.error("Ошибка формата файла. Не CSV!")
        await message.answer("❌ Ошибка формата файла! Попробуйте еще раз...")
        await message.answer(f"Прикрепите файл Показаний формата csv\n"
                             f"Содержимое файла должно быть в таком формате:\n"
                             f"ls;kv;hv;gv;e;date\n"
                             f"Кодировка файла utf-8")
        await delete_file(file_path)


# ====================================================================
# Экспорт лицевых счетов
@admin.callback_query(F.data.startswith('export_users'))
async def export_users(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    await logger.info(f'ID_TG:{callback.from_user.id}|Экспорт Users')
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    sent_mess = await callback.message.answer("🏘 Для экспорта лицевых счетов выберите дом...",
                                              reply_markup=await kb.reply_choice_home())
    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)
    await state.set_state(ChoiceHomeUser.input_home)


@admin.message(ChoiceHomeUser.input_home)
async def process_export_user_home(message: Message, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(message.from_user.id)
    await db.delete_messages(user_state)
    await state.clear()
    await message.answer(f"Собираю данные по дому №{message.text}. Ожидайте ...")
    await logger.info(f'ID_TG:{message.from_user.id}|Собираю данные по дому №{message.text}. Ожидайте ...')

    file_path = f'uploaded_files/export_users_{message.text}.csv'  # Путь к файлу для сохранения данных
    await export_users_to_csv(file_path, message.text)  # Экспортируем данные в CSV

    await send_file_to_user(message, file_path)  # Отправляем файл пользователю

    # Удаляем файл после отправки
    os.remove(file_path)
    await admin_command(message, state)


# ====================================================================
# Экспорт приборов учета

@admin.callback_query(F.data.startswith('export_ipu'))
async def export_users(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    await logger.info(f'ID_TG:{callback.from_user.id}|Экспорт ИПУ')
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.message.answer("Собираю данные. Ожидайте...")
    await logger.info(f'ID_TG:{callback.from_user.id}|Собираю данные. Ожидайте...')
    file_path = f'uploaded_files/export_ipu.csv'  # Путь к файлу для сохранения данных
    await export_ipu_to_csv(file_path)  # Экспортируем данные в CSV

    await send_file_to_user(callback.message, file_path)  # Отправляем файл пользователю

    # Удаляем файл после отправки
    os.remove(file_path)
    sent_mess = await callback.message.answer(f"✅ Данные выгружены")
    await logger.info(f'ID_TG:{callback.from_user.id}|Данные выгружены')
    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)
    await handle_admin_command(callback.from_user.id, callback.message, state)


# ====================================================================
# Экспорт показаний

@admin.callback_query(F.data.startswith('export_pokazaniya'))
async def export_pokazaniya(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    await logger.info(f'ID_TG:{callback.from_user.id}|Экспорт показаний')
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.message.answer("Выбирите месяц:", reply_markup=await kb.month_keyboard())
    await state.set_state(ExportPokazaniya.month)


@admin.message(ExportPokazaniya.month)
async def export_pokazaniyz_month(message: Message, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(message.from_user.id)
    await db.delete_messages(user_state)
    # Сохраняем текст в состоянии
    await state.update_data(month=message.text)
    sent_mess = await message.answer("Выбирите год:", reply_markup=await kb.year_keyboard())
    user_state.last_message_ids.append(sent_mess.message_id)
    await db.update_state(user_state)
    await state.set_state(ExportPokazaniya.year)


@admin.message(ExportPokazaniya.year)
async def export_pokazaniyz_year(message: Message, state: FSMContext):
    db = DataBase()
    user_state = await db.get_state(message.from_user.id)
    await db.delete_messages(user_state)
    await state.update_data(year=message.text)
    data = await state.get_data()
    await state.clear()
    month = data.get('month')
    year = data.get('year')

    await message.answer(f"Вы выбрали месяц: {month}, год: {year}.")
    await logger.info(f'ID_TG:{message.from_user.id}|Вы выбрали месяц: {month}, год: {year}.')
    await message.answer("Собираю данные. Ожидайте...")
    await logger.info(f'ID_TG:{message.from_user.id}|Собираю данные. Ожидайте...')
    file_path = f'uploaded_files/export_pokazaniya_{month}-{year}.csv'  # Путь к файлу для сохранения данных
    # print(file_path)
    if await export_pokazaniya_to_csv(file_path, month, year):  # Экспортируем данные в CSV
        await send_file_to_user(message, file_path)  # Отправляем файл пользователю
        # Удаляем файл после отправки
        os.remove(file_path)
        sent_mess = await message.answer(f"✅ Данные выгружены")
        await logger.info(f'ID_TG:{message.from_user.id}|Данные выгружены')
    else:
        sent_mess = await message.answer(f"❌ Нет данных для экспорта")
        await logger.info(f'ID_TG:{message.from_user.id}|Нет данных для экспорта')
    # user_state.last_message_ids.append(sent_mess.message_id)
    # await db.update_state(user_state)
    await handle_admin_command(message.from_user.id, message, state)


# ====================================================================
# Отправка сообщения пользователям


@admin.callback_query(F.data.startswith('send_message'))
async def send_message(callback: CallbackQuery, state: FSMContext):
    db = DataBase()
    await logger.info(f'ID_TG:{callback.from_user.id}|Отправка сообщений')
    user_state = await db.get_state(callback.from_user.id)
    await db.delete_messages(user_state)
    await callback.message.answer("Напишите текст сообщения:")
    await state.set_state(SendMess.mess)


@admin.message(SendMess.mess)
async def process_send(message: Message, state: FSMContext):
    await state.clear()
    mess_text = message.text
    await logger.info(f'ID_TG:{message.from_user.id}|Сообщ:{mess_text}')
    db = DataBase()
    await message.answer("Идет отправка. Ожидайте... ")
    # список id telegarma
    result = await db.get_users_bot()

    if result:
        res = await send_mess(result, mess_text)
        await message.answer(f"✅ Сообщение успешно отправлено. {res}шт")
        await logger.info(f'ID_TG:{message.from_user.id}|Сообщение успешно отправлено.')
        await handle_admin_command(message.from_user.id, message, state)
    else:
        await message.answer("❌ Нет пользователей")
        await logger.info(f'ID_TG:{message.from_user.id}|Нет пользователей')


# =============FUNCTIN==================
async def send_mess(ids, message_text):
    i = 0
    from main import bot
    for user in ids:
        try:
            await bot.send_message(user.id_tg, message_text)
            await logger.info(f"Сообщение отправлено пользователю {user.id_tg}.")
            i += 1
        except Exception as e:
            await logger.error(f"Не удалось отправить сообщение пользователю {user.id_tg}: {e}")
    return i


# =================================================
async def export_pokazaniya_to_csv(file_path, month, year):
    month_number = month_mapping.get(month)
    await logger.info(f"Запрос показаний месяц={month_number}, год={year}")
    # Создаем директорию, если её нет
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    db = DataBase()
    results = await db.get_pokazaniya(month_number, year)
    # print(f"results={results}")
    if not results:
        return False

    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=';')
            writer.writerow(['ls', 'kv', 'hv', 'gv', 'e', 'date'])  # Записываем заголовки

            for result in results:
                await logger.info(f"Записываем в файл пользователя: {result.ls}, {result.kv}, {result.hv}, {result.gv},"
                            f"{result.e}, {result.date}")
                writer.writerow([result.ls, result.kv, result.hv, result.gv, result.e, result.date])  # Записываем
                # данные
            await logger.info(f"Данные успешно экспортированы в файл: {file_path}")
            return True

    except Exception as e:
        await logger.error(f"Ошибка при экспорте данных в CSV: {e}")


async def export_users_to_csv(file_path, home):
    """Экспорт данных пользователей в CSV-файл."""
    # Создаем директорию, если её нет
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=';')
            writer.writerow(['ls', 'home', 'kv', 'address'])  # Записываем заголовки
            db = DataBase()
            users = await db.get_users_home(home)

            if not users:
                await logger.warning(f"Не найдены пользователи для дома {home}.")
                return

            for user in users:
                await logger.info(f"Записываем в файл пользователя: {user.ls}, {user.home}, {user.kv}, {user.address}")
                writer.writerow([user.ls, user.home, user.kv, user.address])  # Записываем данные
        await logger.info(f"Данные успешно экспортированы в файл: {file_path}")
    except Exception as e:
        await logger.error(f"Ошибка при экспорте данных в CSV: {e}")


# ========================================================================
async def export_ipu_to_csv(file_path):
    """Экспорт данных ИПУ в CSV-файл."""
    # Создаем директорию, если её нет
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=';')
            writer.writerow(['Лицевой', 'Наименование ПУ', 'Заводской номер', 'Дата следующей поверки', 'Место установки' ,'Тип счетчика'])  # Записываем заголовки
            db = DataBase()
            ipus = await db.get_ipu_all()

            if not ipus:
                await logger.warning(f"Не найдены приборы учета.")
                return

            for ipu in ipus:
                await logger.info(f"Записываем в файл пу: {ipu.ls}, {ipu.name}, {ipu.number}, {ipu.data_pov_next},"
                            f"{ipu.location}, {type_mapping.get(ipu.type)}")
                writer.writerow([ipu.ls, ipu.name, ipu.number, ipu.data_pov_next, ipu.location, type_mapping.get(ipu.type)])  #
                # Записываем данные
        await logger.info(f"Данные успешно экспортированы в файл: {file_path}")
    except Exception as e:
        await logger.error(f"Ошибка при экспорте данных в CSV: {e}")


# ========================================================================
async def send_file_to_user(message: Message, file_path: str):
    """Отправка файла пользователю."""
    try:
        # Используем InputFile для отправки файла
        input_file = FSInputFile(file_path)  # Создаем InputFile с путем к файлу
        await message.answer_document(input_file)  # Отправляем файл пользователю
    except FileNotFoundError:
        await message.answer("Файл не найден.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при отправке файла: {e}")


# ========================================================================

async def add_user_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        rows = csv.reader(csv_file, delimiter=';')
        headers = next(rows)

        # Проверяем заголовки
        headers_full = ['ls', 'home', 'kv', 'address', 'flag']
        headers_partial = ['ls', 'home', 'kv', 'address']

        if headers != headers_full and headers != headers_partial:
            await logger.error("Неверные заголовки файла")
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
        print(f"headers={headers}")
        # Проверяем заголовки
        headers_full = ['Лицевой', 'Наименование ПУ', 'Заводской номер', 'Дата следующей поверки', 'Место установки', 'Тип счетчика', 'flag']
        headers_partial = ['Лицевой', 'Наименование ПУ', 'Заводской номер', 'Дата следующей поверки', 'Место установки', 'Тип счетчика']

        if headers != headers_full and headers != headers_partial:
            await logger.error("Неверные заголовки файла")
            return False

        db = DataBase()
        for row in rows:
            # print(row)
            ls, name, number, data_pov_next, location, type_ = row[:6]
            flag_value = row[6].strip().lower() == '1' if len(row) > 6 else False  # Проверка флага
            type_key = next((k for k, v in type_mapping.items() if v == type_), None)
            if flag_value:
                await db.del_ipu(ls, type_key)
            else:

                await db.add_or_update_ipu(ls, name, number, data_pov_next, location, type_key)

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
            await logger.error("Неверные заголовки файла")
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
async def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        await logger.info("Файл успешно удален!")
    else:
        await logger.info("Ошибка удаления! Файл не существует.")

# =====================

# =====================
# =====================

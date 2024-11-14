from sqlalchemy import select, and_, delete, case, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from database.models import *
import os
import logging
from datetime import date
from datetime import datetime
# from app.log import Loger

# # Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# logger = Loger(Data)
# logger.get_name_log(__name__)


type_mapping = {
    'hv': 'ХВС',
    'gv': 'ГВС',
    'e': 'ЭЛ-ВО'
}


class DataBase:
    def __init__(self):
        self.connect = os.getenv('DB_URL')
        self.async_engine = create_async_engine(url=self.connect, echo=False)
        self.Session = async_sessionmaker(bind=self.async_engine, class_=AsyncSession)

    async def create_db(self):
        async with self.async_engine.begin() as connect:
            await connect.run_sync(Base.metadata.create_all)

    async def get_state(self, id_tg: int):
        async with self.Session() as session:
            # Попытка получить состояние пользователя по user_id
            state = await session.scalar(select(UserState).where(UserState.user_id == id_tg))

            if state is None:
                logger.info(f'Состояние не найдено для user_state_id: {id_tg}. Создание нового состояния.')
                # Если состояния нет, создаем новое
                state = UserState(user_id=id_tg)
                session.add(state)
                await session.commit()  # Сохраняем изменения
                state = await session.scalar(select(UserState).where(UserState.user_id == id_tg))
                logger.info(f'Создано состояние user_state:{state.user_id}')
                return state
            else:
                logger.info(f'Получено состояние для user_state_id: {id_tg}.')

                return state

    async def get_userbot(self, tg: int):
        async with self.Session() as session:
            result = await session.execute(select(UsersBot).where(UsersBot.id_tg == tg))
            return result.scalars()

    async def get_userbot_ls(self, ls: int):
        async with self.Session() as session:
            result = await session.execute(select(UsersBot).where(UsersBot.ls == ls))
            return result.scalar()

    async def update_state(self, state: UserState):
        async with self.Session() as session:
            # Убедитесь, что объект связан с текущей сессией
            existing_state = await session.execute(select(UserState).where(UserState.user_id == state.user_id))
            current_state = existing_state.scalars().one_or_none()

            if current_state:
                # Обновление атрибутов
                current_state.last_message_ids = state.last_message_ids
                current_state.kv = state.kv
                current_state.ls = state.ls
                current_state.home = state.home

                # Сохранение изменений
                await session.commit()
                return current_state  # Возвращаем обновленный объект
            else:
                return None  # Состояние не найдено

    async def delete_messages(self, state):
        if state.last_message_ids:
            from main import bot
            for lst in state.last_message_ids:
                try:
                    await bot.delete_message(chat_id=state.user_id, message_id=lst)
                except Exception as e:
                    logger.error(f"Ошибка при удалении сообщения: {e}")
            state.last_message_ids.clear()

    async def get_users(self, ls: int, kv: int):
        async with self.Session() as session:
            result = await session.execute(select(Users).where(and_(Users.ls == ls, Users.kv == kv)))
            return result.scalar()

    async def get_user_ls(self, ls: int):
        async with self.Session() as session:
            result = await session.execute(select(Users).where(Users.ls == ls))
            return result.scalar()

    async def create_userbot(self, **kwargs):
        logger.info(f"Запись в бд id_tg:{kwargs['id_tg']};ls:{kwargs['ls']};home:{kwargs['home']};kv:{kwargs['kv']}")
        async with self.Session() as session:
            try:
                session.add(UsersBot(**kwargs))
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()  # Откатить изменения в случае ошибки
                logger.error(f"Ошибка при добавлении: {e}")
                return False

    async def get_ipu(self, ls: int):
        logger.info(f"Получить по лицевому №{ls} список счетчиков")
        async with self.Session() as session:
            # meter_result = await session.execute(select(MeterDev).where(MeterDev.ls == ls))
            meter_result = await session.execute(
                select(MeterDev)
                .where(MeterDev.ls == ls)
                .order_by(case(
                    {
                        'hv': 1,
                        'gv': 2,
                        'e': 3
                    },
                    value=MeterDev.type
                ))
            )
            return meter_result.scalars().all()

    async def get_address(self, ls: int):
        async with self.Session() as session:
            result = await session.execute(select(Users).where(Users.ls == ls))
            return result.scalar()

    async def del_ls(self, id_tg: int, ls: int):
        async with self.Session() as session:
            result = await session.execute(delete(UsersBot).where(and_(UsersBot.id_tg == id_tg), (UsersBot.ls == ls)))
            await session.commit()
            # Проверяем количество удаленных строк
            return result.rowcount > 0

    async def get_pokazaniya_last(self, ls, type_ipu):
        async with self.Session() as session:
            result = await session.execute(
                select(Pokazaniya).where(Pokazaniya.ls == ls, getattr(Pokazaniya, type_ipu).isnot(None)).order_by(
                    Pokazaniya.date.desc())
            )
            return result.scalars().first()

    async def add_or_update_pokazaniya(self, ls: int, kv: int, type_ipu: str, value: str):
        # Получаем текущую дату
        current_date = date.today()

        async with self.Session() as session:
            # Проверяем, существует ли запись с такими же ls, kv и текущей датой
            result = await session.execute(
                select(Pokazaniya).where(
                    Pokazaniya.ls == ls,
                    Pokazaniya.kv == kv,
                    Pokazaniya.date == current_date
                )
            )

            existing_record = result.scalars().first()  # Получаем первую подходящую запись

            if existing_record:
                # Если запись существует, обновляем соответствующее поле в зависимости от type_ipu
                logger.info(f"Обновляем запись: {existing_record}")
                if type_ipu == 'hv':
                    existing_record.hv = value
                elif type_ipu == 'gv':
                    existing_record.gv = value
                elif type_ipu == 'e':
                    existing_record.e = value

                await session.commit()  # Сохраняем изменения
                logger.info("Запись обновлена.")
            else:
                # Если записи нет, создаем новую
                new_record = Pokazaniya(ls=ls, kv=kv, date=current_date)
                logger.info("Создаем новую запись с показаниями")

                # Устанавливаем значение поля в зависимости от type_ipu
                if type_ipu == 'hv':
                    new_record.hv = value
                elif type_ipu == 'gv':
                    new_record.gv = value
                elif type_ipu == 'e':
                    new_record.e = value

                session.add(new_record)  # Добавляем новую запись в сессию
                await session.commit()  # Сохраняем новую запись
                logger.info("Новая запись сохранена.")

    async def check_admin(self, id_tg):
        async with self.Session() as session:
            result = await session.execute(select(AdminBot).where(AdminBot.id_tg == id_tg))
            return result.scalar()

    async def add_or_update_user(self, ls, home, kv, address):
        async with self.Session() as session:
            # Проверяем, существует ли запись с такими же ls, kv и текущей датой
            result = await session.execute(select(Users).where(Users.ls == ls))
            existing_record = result.scalars().first()  # Получаем первую подходящую запись

            if existing_record:
                logger.info(f"Обновляем запись: {existing_record}")
                existing_record.ls = ls
                existing_record.home = home
                existing_record.kv = kv
                existing_record.address = address
                await session.commit()  # Сохраняем изменения
                logger.info("Запись обновлена.")
            else:
                # Если записи нет, создаем новую
                new_record = Users(ls=ls, home=home, kv=kv, address=address)
                logger.info("Создаем новую запись с пользователем")
                session.add(new_record)  # Добавляем новую запись в сессию
                await session.commit()  # Сохраняем новую запись
                logger.info("Новая запись сохранена.")

    async def add_or_update_ipu(self, ls, name, number, data_pov_next, location, type_):
        async with self.Session() as session:
            # Проверяем, существует ли запись с такими же ls, kv и текущей датой
            result = await session.execute(
                select(MeterDev).where(
                    and_(MeterDev.ls == ls, MeterDev.type == type_)
                )
            )
            existing_record = result.scalars().first()  # Получаем первую подходящую запись

            if existing_record:
                logger.info(f"Обновляем запись: {existing_record}")
                existing_record.ls = ls
                existing_record.name = name
                existing_record.number = number
                existing_record.data_pov_next = date.fromisoformat(data_pov_next) if data_pov_next else None
                existing_record.location = location
                existing_record.type = type_
                await session.commit()  # Сохраняем изменения
                logger.info("Запись обновлена.")
            else:
                # Если записи нет, создаем новую
                new_record = MeterDev(
                    ls=ls,
                    name=name,
                    number=number,
                    data_pov_next=date.fromisoformat(data_pov_next) if data_pov_next else None,
                    location=location,
                    type=type_
                )
                logger.info(f"Создаем новую запись ipu ls={ls} {type_mapping.get(type_)}")
                session.add(new_record)  # Добавляем новую запись в сессию
                await session.commit()  # Сохраняем новую запись
                logger.info("Новая запись сохранена.")

    async def add_or_update_pokaz_admin(self, ls, kv, hv, gv, e, date):
        async with self.Session() as session:
            # Проверяем, существует ли запись с такими же ls, kv и текущей датой
            result = await session.execute(
                select(Pokazaniya).where(
                    and_(Pokazaniya.ls == ls, Pokazaniya.date == date)
                )
            )
            existing_record = result.scalars().first()  # Получаем первую подходящую запись
            # Преобразуем строку даты в объект date
            date_value = datetime.strptime(date, '%Y-%m-%d').date()
            if existing_record:
                logger.info(f"Обновляем запись: {existing_record}")
                existing_record.ls = ls
                existing_record.kv = kv
                existing_record.hv = hv
                existing_record.gv = gv
                existing_record.e = e
                existing_record.date = date_value
                await session.commit()  # Сохраняем изменения
                logger.info("Запись обновлена.")
            else:
                # Если записи нет, создаем новую
                new_record = Pokazaniya(
                    ls=ls,
                    kv=kv,
                    hv=hv,
                    gv=gv,
                    e=e,
                    date=date_value
                )
                logger.info("Создаем новую запись показаний")
                session.add(new_record)  # Добавляем новую запись в сессию
                await session.commit()  # Сохраняем новую запись
                logger.info("Новая запись сохранена.")

    async def del_user(self, ls):
        async with self.Session() as session:
            result = await session.execute(
                delete(Users).where(
                    Users.ls == ls
                )
            )
            await session.commit()

            # Проверяем количество удаленных строк
            if result.rowcount == 0:
                logger.warning(f"Запись с ls={ls} не найдена для удаления.")
                return False  # Запись не найдена
            else:
                logger.info(f"Запись с ls={ls} удалена.")
                return True  # Запись успешно удалена

    async def del_ipu(self, ls, type_):
        async with self.Session() as session:
            result = await session.execute(
                delete(MeterDev).where(
                    and_(MeterDev.ls == ls, MeterDev.type == type_)
                )
            )
            await session.commit()

            # Проверяем количество удаленных строк
            if result.rowcount == 0:
                logger.warning(f"Запись с ls={ls} {type_mapping.get(type_)}  не найдена для удаления.")
                return False  # Запись не найдена
            else:
                logger.info(f"Запись с ls={ls} {type_mapping.get(type_)} удалена.")
                return True  # Запись успешно удалена

    async def pokaz_admin_del(self, ls, data: str):
        date = datetime.strptime(data, "%Y-%m-%d").date()
        async with self.Session() as session:
            result = await session.execute(
                delete(Pokazaniya).where(
                    and_(Pokazaniya.ls == ls, Pokazaniya.date == date)
                )
            )
            await session.commit()

            # Проверяем количество удаленных строк
            if result.rowcount == 0:
                logger.warning(f"Запись с ls={ls} {date}  не найдена для удаления.")
                return False  # Запись не найдена
            else:
                logger.info(f"Запись с ls={ls} {date} удалена.")
                return True  # Запись успешно удалена

    async def get_users_home(self, home):
        async with self.Session() as session:
            result = await session.execute(
                select(Users).where(Users.home == home).order_by(Users.kv)
            )
            return result.scalars().all()

    async def get_ipu_all(self):
        async with self.Session() as session:
            result = await session.execute(
                select(MeterDev).order_by(MeterDev.ls)
            )
            return result.scalars().all()

    async def get_pokazaniya(self, mon: str, year: str):
        async with self.Session() as session:
            # Преобразуем месяц и год в целые числа
            month = int(mon)  # Преобразование месяца в целое число
            year = int(year)  # Преобразование года в целое число

            # Выполняем запрос с условиями по месяцу и году
            result = await session.execute(
                select(Pokazaniya)
                .where(
                    func.strftime('%m', Pokazaniya.date) == f'{month:02d}',  # Форматируем месяц
                    func.strftime('%Y', Pokazaniya.date) == str(year)  # Сравниваем год
                )
                .order_by(Pokazaniya.ls)
            )
            return result.scalars().all()

    async def get_users_bot(self):
        async with self.Session() as session:
            result = await session.execute(
                select(UsersBot)
            )
        return result.scalars().all()

    async def get_pokazaniya_last_prev(self, ls: int, target_date: str):
        async with self.Session() as session:
            result = await session.execute(
                select(Pokazaniya)
                .where(
                    and_(
                        Pokazaniya.ls == ls,
                        Pokazaniya.date < target_date
                    )
                )
                .order_by(Pokazaniya.date.desc())
                .limit(1)
            )
            return result.scalars().first()  # Получаем первую запись или None

    async def log_to_db(self, level: str, message: str, logger_name: str):
        async with self.Session() as session:
            log_entry = Logs(
                timestamp=datetime.now(),  # Здесь можете использовать datetime.now().isoformat() для меток времени
                name=logger_name,
                level=level,
                message=message
            )
            session.add(log_entry)
            await session.commit()


# logger = Loger(DataBase)
# logger.get_name_log(__name__)

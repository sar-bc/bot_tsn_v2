from sqlalchemy import (ForeignKey, String, BigInteger,
                        TIMESTAMP, Column, func, Integer,
                        Text, CheckConstraint, Date, DateTime, Boolean, JSON)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


####################################
class AdminBot(Base):
    __tablename__ = 'AdminBot'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_tg = Column(BigInteger, nullable=False)
    username = Column(String(100), nullable=True)

    def __repr__(self):
        return (f"<AdminBot(id={self.id}, id_tg={self.id_tg}, username={self.username})>")


####################################
class UsersBot(Base):
    __tablename__ = 'UsersBot'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_tg = Column(BigInteger, nullable=False)
    ls = Column(Integer)
    home = Column(Integer)
    kv = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return (f"<UsersBot(id={self.id}, id_tg={self.id_tg}, ls={self.ls}, "
                f"kv={self.kv}, created_at={self.created_at}, is_active={self.is_active})>")


####################################
class Users(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ls = Column(Integer, nullable=False, unique=True)
    home = Column(Integer, nullable=False)
    kv = Column(Integer, nullable=False)
    address = Column(Text)

    # meters = relationship('MeterDev', back_populates='user')

    def __repr__(self):  # Исправлено на __repr__
        return f"<Users(id={self.id}, ls={self.ls}, home={self.home}, kv={self.kv}, address='{self.address}')>"


####################################
class MeterDev(Base):
    __tablename__ = 'MeterDev'  # Исправлено на __tablename__

    id = Column(Integer, primary_key=True, autoincrement=True)
    # ls = Column(Integer, ForeignKey('Users.ls'), nullable=False)
    ls = Column(Integer, nullable=False)
    name = Column(String(250), nullable=True, default='')
    number = Column(String(100), nullable=True, default='')
    data_pov_next = Column(Date, nullable=True)
    location = Column(String(50), nullable=True, default='')
    type = Column(String(3), default='hv', nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('hv', 'gv', 'e')", name="check_type"),
    )

    # Связь с пользователем
    # user = relationship('Users', back_populates='meters')

    def __repr__(self):  # Определение метода __repr__
        return (f"<MeterDev(id={self.id}, ls={self.ls}, name='{self.name}', "
                f"number='{self.number}', data_pov_next='{self.data_pov_next}', "
                f"type='{self.type}')>")


####################################
class Pokazaniya(Base):
    __tablename__ = 'Pokazaniya'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ls = Column(Integer, nullable=False)
    kv = Column(Integer, nullable=False)
    hv = Column(String(10))
    gv = Column(String(10))
    e = Column(String(10))
    date = Column(Date, nullable=False)

    def __repr__(self):
        return (f"<Pokazaniya(id={self.id}, ls={self.ls}, kv={self.kv}, "
                f"hv={self.hv}, gv={self.gv}, e={self.e}, date='{self.date}')>")


####################################
# class PokazaniyaUser(Base):
#     __tablename__ = 'PokazaniyaUser'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     ls = Column(Integer, nullable=False)
#     kv = Column(Integer, nullable=False)
#     hv = Column(Integer)
#     gv = Column(Integer)
#     e = Column(Integer)
#     date = Column(Date, nullable=False)

#     def __repr__(self):
#         return (f"<PokazaniyaUser(id={self.id}, ls={self.ls}, kv={self.kv}, "
#                 f"hv={self.hv}, gv={self.gv}, e={self.e}, date='{self.date}')>")


####################################

class UserState(Base):
    __tablename__ = 'UserState'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    last_message_ids = Column(JSON, default=list)  # Поддержка JSON
    kv = Column(Integer, default=0)
    ls = Column(Integer, default=0)
    home = Column(Integer, default=0)

    def __repr__(self):
        return (f"<UserState(id={self.id}, user_id={self.user_id}, "
                f"last_message_ids={self.last_message_ids}, "
                f"kv={self.kv}, ls={self.ls}, home={self.home})>")

####################################


class Logs(Base):
    __tablename__ = 'Logs'  # Имя таблицы в базе данных

    id = Column(Integer, primary_key=True, autoincrement=True)  # Уникальный идентификатор
    timestamp = Column(DateTime, nullable=False)  # Временная метка
    name = Column(Text, nullable=False)  # Имя логгера
    level = Column(Text, nullable=False)  # Уровень логирования
    message = Column(Text, nullable=False)  # Сообщение лога

    def __repr__(self):
        return (f"<Log(id={self.id}, timestamp='{self.timestamp}', "
                f"name='{self.name}', level='{self.level}', "
                f"message='{self.message}')>")


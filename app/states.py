from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class AddLs(StatesGroup):
    ls = State()
    kv = State()


class AddPokazaniya(StatesGroup):
    input = State()
    ls = State()
    kv = State()
    type_ipu = State()
    last_input = State()
    last_data = State()


class ImportUsers(StatesGroup):
    choice = State()
    input_file = State()


class ImportIpu(StatesGroup):
    choice = State()
    input_file = State()


class ImportPokazaniya(StatesGroup):
    choice = State()
    input_file = State()


class ChoiceHomeUser(StatesGroup):
    input_home = State()


class ExportPokazaniya(StatesGroup):
    month = State()
    year = State()


class SendMess(StatesGroup):
    mess = State()

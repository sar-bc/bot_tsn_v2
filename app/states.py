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


class ImportUsers(StatesGroup):
    choice = State()
    input_file = State()


class ImportIpu(StatesGroup):
    choice = State()
    input_file = State()


class ImportPokazaniya(StatesGroup):
    choice = State()
    input_file = State()


class ChoiceHome(StatesGroup):
    input_home = State()

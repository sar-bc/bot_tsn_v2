from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class AddLs(StatesGroup):
    ls = State()
    kv = State()


class AddPokazaniya(StatesGroup):
    input = State()
    ls = State()
    type_ipu = State()
    last_input = State()
    hv = State()
    gv = State()
    e = State()

    # last_hv = State()
    # last_gv = State()
    # last_e = State()

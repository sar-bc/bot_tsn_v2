from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class AddLs(StatesGroup):
    ls = State()
    kv = State()


from aiogram import Router
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
import app.keyboards as kb

type_mapping = {
    'hv': 'ХВС',
    'gv': 'ГВС',
    'e': 'ЭЛ-ВО'
}

admin = Router()

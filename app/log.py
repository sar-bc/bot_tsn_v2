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
from datetime import datetime
import asyncio
import threading


class Loger:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.name_doc = __name__
        self.db = DataBase()

    def get_name_log(self, name_doc):
        self.name_doc = name_doc

    async def log_info(self, text: str):
        await self.db.log_to_db("INFO", text, self.name_doc)
        print(f"{datetime.now()} - {self.name_doc} - INFO - {text}")

    def run_log_info(self, text: str):
        asyncio.run(self.log_info(text))

    def info(self, text: str):
        # Запускаем асинхронный лог в отдельном потоке
        threading.Thread(target=self.run_log_info, args=(text,)).start()

    async def log_error(self, text: str):
        await self.db.log_to_db("ERROR", text, self.name_doc)
        print(f"{datetime.now()} - {self.name_doc} - ERROR - {text}")

    def run_log_error(self, text: str):
        asyncio.run(self.log_error(text))

    def error(self, text: str):
        # Запускаем асинхронный лог в отдельном потоке
        threading.Thread(target=self.run_log_error, args=(text,)).start()

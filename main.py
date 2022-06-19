from aiogram import executor
from dispatcher import dp
import asyncio
import handlers

from db import BotDB
BotDB = BotDB('app.db')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=handlers.actions.on_startup)

# main.py

import asyncio
import sqlite3
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_PATH = 'support_bot.db'

def connect_db():
    return sqlite3.connect(DB_PATH)


def filter_buttons():
    builder = InlineKeyboardBuilder()
    builder.button(text="7 дней", callback_data="filter_7")
    builder.button(text="30 дней", callback_data="filter_30")
    builder.button(text="Год", callback_data="filter_365")
    builder.button(text="Произвольный период", callback_data="filter_custom")
    builder.adjust(2)
    return builder.as_markup()


@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Привет! Используй /exotic для аналитики 🦎")

@dp.message(F.text == "/exotic")
async def cmd_exotic(message: types.Message):
    await message.answer("Выбери период для аналитики:", reply_markup=filter_buttons())

@dp.callback_query(F.data.startswith("filter_"))
async def handle_filter(callback: types.CallbackQuery):
    days = int(callback.data.split("_")[1])
    date_from = datetime.now() - timedelta(days=days)

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT animal_type, COUNT(*) FROM exotic_consultations
           WHERE consultation_date >= ?
           GROUP BY animal_type''',
        (date_from.strftime('%Y-%m-%d %H:%M:%S'),)
    )
    data = cursor.fetchall()
    conn.close()

    if not data:
        await callback.message.answer("Нет данных за выбранный период.")
        return

    text = f"📊 Консультации за последние {days} дней:\n\n"
    for animal, count in data:
        text += f"🐾 {animal}: {count}\n"

    await callback.message.answer(text)
    await callback.answer()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import sqlite3
import matplotlib.pyplot as plt
import io
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Клавиатура фильтров ===
filter_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="7 дней", callback_data="filter_7")],
    [InlineKeyboardButton(text="30 дней", callback_data="filter_30")],
    [InlineKeyboardButton(text="Год", callback_data="filter_365")],
    [InlineKeyboardButton(text="Произвольный период", callback_data="filter_custom")],
])

# === Подключение к БД ===
def connect_db():
    return sqlite3.connect("support_bot.db")

# === Команда /start ===
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот аналитики по экзотическим животным 🦎\n\nИспользуй /exotic")

# === Команда /exotic ===
@dp.message(F.text == "/exotic")
async def cmd_exotic(message: Message):
    await message.answer("Выбери период:", reply_markup=filter_keyboard)

# === Обработка фильтрации ===
@dp.callback_query(F.data.startswith("filter_"))
async def filter_consultations(callback: CallbackQuery):
    filter_type = callback.data.split("_")[1]

    conn = connect_db()
    cursor = conn.cursor()

    query = ""
    params = ()

    if filter_type == "7":
        query = '''SELECT animal_type, COUNT(*) FROM exotic_consultations
                   WHERE consultation_date >= datetime('now', '-7 days')
                   GROUP BY animal_type'''
    elif filter_type == "30":
        query = '''SELECT animal_type, COUNT(*) FROM exotic_consultations
                   WHERE consultation_date >= datetime('now', '-30 days')
                   GROUP BY animal_type'''
    elif filter_type == "365":
        query = '''SELECT animal_type, COUNT(*) FROM exotic_consultations
                   WHERE consultation_date >= datetime('now', '-365 days')
                   GROUP BY animal_type'''
    else:
        await callback.answer("Неверный фильтр", show_alert=True)
        return

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.message.answer("Нет данных за выбранный период.")
        return

    text = "\U0001F4CA Статистика консультаций:\n\n"
    for animal, count in rows:
        text += f"🐾 {animal}: {count}\n"

    await callback.message.answer(text)
    await callback.answer()

# === FSM состояние ===
class DateRangeState(StatesGroup):
    start_date = State()
    end_date = State()

# === Кастомный диапазон ===
@dp.callback_query(F.data == "filter_custom")
async def start_custom_filter(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите начальную дату в формате YYYY-MM-DD:")
    await state.set_state(DateRangeState.start_date)
    await callback.answer()

@dp.message(DateRangeState.start_date)
async def set_start_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("❗ Неверный формат. Введите дату в формате YYYY-MM-DD:")
        return
    await state.update_data(start_date=date_text)
    await message.answer("Теперь введите конечную дату в формате YYYY-MM-DD:")
    await state.set_state(DateRangeState.end_date)

@dp.message(DateRangeState.end_date)
async def set_end_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("❗ Неверный формат. Введите дату в формате YYYY-MM-DD:")
        return

    data = await state.get_data()
    start_date = data['start_date']
    end_date = date_text

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT animal_type, COUNT(*) FROM exotic_consultations
        WHERE consultation_date BETWEEN ? AND ?
        GROUP BY animal_type
    ''', (start_date + " 00:00:00", end_date + " 23:59:59"))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("Нет данных за выбранный период.")
    else:
        text = f"\U0001F4CA Консультации с {start_date} по {end_date}:\n\n"
        for animal, count in rows:
            text += f"🐾 {animal}: {count}\n"
        await message.answer(text)

    await state.clear()

# === Запуск ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


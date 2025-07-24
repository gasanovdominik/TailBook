import asyncio
import io
import re
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


# ========== FSM Состояния ==========
class DateRangeState(StatesGroup):
    start_date = State()
    end_date = State()


# ========== Клавиатура фильтрации ==========
filter_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="7 дней", callback_data="filter_7")],
    [InlineKeyboardButton(text="30 дней", callback_data="filter_30")],
    [InlineKeyboardButton(text="Год", callback_data="filter_365")],
    [InlineKeyboardButton(text="Произвольный период", callback_data="filter_custom")]
])


# ========== Подключение к БД ==========
def connect_db():
    return sqlite3.connect("support_bot.db")


# ========== Горизонтальный график ==========
def generate_horizontal_chart(start_date: str, end_date: str) -> io.BytesIO | None:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT animal_type, COUNT(*) FROM exotic_consultations
        WHERE consultation_date BETWEEN ? AND ?
        GROUP BY animal_type
    ''', (start_date + " 00:00:00", end_date + " 23:59:59"))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return None

    animals = [row[0] for row in data]
    counts = [row[1] for row in data]

    plt.figure(figsize=(8, 5))
    bars = plt.barh(animals, counts, color='mediumseagreen')
    plt.xlabel("Количество консультаций")
    plt.title("Консультации по типам животных")

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.1, bar.get_y() + bar.get_height() / 2, str(int(width)), va='center')

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf


# ========== Команда /start ==========
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я бот аналитики по экзотическим животным 🦎\n\nИспользуй /exotic")


# ========== Команда /exotic ==========
@dp.message(Command("exotic"))
async def exotic_handler(message: Message):
    await message.answer("Выбери период:", reply_markup=filter_keyboard)


# ========== Кнопки 7, 30, 365 дней ==========
@dp.callback_query(F.data.startswith("filter_"))
async def filter_predefined(callback: CallbackQuery):
    period = callback.data.split("_")[1]
    days = int(period)
    end = datetime.now()
    start = end - timedelta(days=days)

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT animal_type, COUNT(*) FROM exotic_consultations
        WHERE consultation_date BETWEEN ? AND ?
        GROUP BY animal_type
    ''', (start.strftime('%Y-%m-%d 00:00:00'), end.strftime('%Y-%m-%d 23:59:59')))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.message.answer("Нет данных за этот период.")
        return

    text = f"📊 Статистика консультаций:\n\n"
    for animal, count in rows:
        text += f"🐾 {animal}: {count}\n"
    await callback.message.answer(text)

    chart = generate_horizontal_chart(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    if chart:
        await callback.message.answer_photo(chart, caption="График по типам животных 🐾")

    await callback.answer()


# ========== Кнопка "Произвольный период" ==========
@dp.callback_query(F.data == "filter_custom")
async def start_custom_filter(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите начальную дату в формате YYYY-MM-DD:")
    await state.set_state(DateRangeState.start_date)
    await callback.answer()


# ========== Ввод первой даты ==========
@dp.message(DateRangeState.start_date)
async def set_start_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("❗ Неверный формат. Введите дату в формате YYYY-MM-DD:")
        return

    await state.update_data(start_date=date_text)
    await message.answer("Теперь введите конечную дату в формате YYYY-MM-DD:")
    await state.set_state(DateRangeState.end_date)


# ========== Ввод второй даты и вывод графика ==========
@dp.message(DateRangeState.end_date)
async def set_end_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("❗ Неверный формат. Введите дату в формате YYYY-MM-DD:")
        return

    data = await state.get_data()
    start_date = data["start_date"]
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
        text = f"📊 Консультации с {start_date} по {end_date}:\n\n"
        for animal, count in rows:
            text += f"🐾 {animal}: {count}\n"
        await message.answer(text)

        chart = generate_horizontal_chart(start_date, end_date)
        if chart:
            await message.answer_photo(photo=chart, caption="График по типам животных 🐾")

    await state.clear()


# ========== Запуск бота ==========
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))



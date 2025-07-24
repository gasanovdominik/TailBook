import os
import sqlite3
import re
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils import generate_horizontal_chart

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("API_TOKEN"))
dp = Dispatcher()

# === FSM ===
class DateRangeState(StatesGroup):
    start_date = State()
    end_date = State()

# === DB connect ===
def connect_db():
    return sqlite3.connect("support_bot.db")

# === Inline кнопки ===
def get_exotic_buttons():
    kb = InlineKeyboardBuilder()
    kb.button(text="7 дней", callback_data="filter_7")
    kb.button(text="30 дней", callback_data="filter_30")
    kb.button(text="Год", callback_data="filter_365")
    kb.button(text="Произвольный период", callback_data="filter_custom")
    kb.adjust(1)
    return kb.as_markup()

# === /start ===
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Я бот аналитики по экзотическим животным 🦎\n\nИспользуй /exotic")

# === /exotic ===
@dp.message(Command("exotic"))
async def exotic_handler(message: Message):
    await message.answer("Выбери период:", reply_markup=get_exotic_buttons())

# === Кнопки периодов ===
@dp.callback_query(F.data.startswith("filter_"))
async def filter_callback(callback: CallbackQuery):
    code = callback.data.split("_")[1]
    if code == "custom":
        await callback.message.answer("Введите начальную дату в формате YYYY-MM-DD:")
        await dp.fsm.set_state(callback.from_user.id, DateRangeState.start_date.state)
        await callback.answer()
        return

    days = int(code)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT animal_type, COUNT(*) FROM exotic_consultations
        WHERE consultation_date BETWEEN ? AND ?
        GROUP BY animal_type
    ''', (start_date.strftime("%Y-%m-%d 00:00:00"), end_date.strftime("%Y-%m-%d 23:59:59")))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.message.answer("Нет данных за выбранный период.")
    else:
        text = "\ud83d\udcca Статистика консультаций:\n\n"
        for animal, count in rows:
            text += f"\ud83d\udc3e {animal}: {count}\n"
        await callback.message.answer(text)

        chart = generate_horizontal_chart(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if chart:
            await callback.message.answer_photo(photo=chart, caption="График по типам животных")
    await callback.answer()

# === FSM: кастомные даты ===
@dp.message(DateRangeState.start_date)
async def set_start_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("Неверный формат. Введите дату в формате YYYY-MM-DD:")
        return
    await state.update_data(start_date=date_text)
    await message.answer("Теперь введите конечную дату в формате YYYY-MM-DD:")
    await state.set_state(DateRangeState.end_date)

@dp.message(DateRangeState.end_date)
async def set_end_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("Неверный формат. Введите дату в формате YYYY-MM-DD:")
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
        text = f"\ud83d\udcca Консультации с {start_date} по {end_date}:\n\n"
        for animal, count in rows:
            text += f"\ud83d\udc3e {animal}: {count}\n"
        await message.answer(text)

        chart = generate_horizontal_chart(start_date, end_date)
        if chart:
            await message.answer_photo(photo=chart, caption="График по типам животных")

    await state.clear()

# === /admin ===
@dp.message(Command("admin"))
async def admin_command(message: Message):
    admin_id = int(os.getenv("ADMIN_ID", "0"))
    if message.from_user.id != admin_id:
        await message.answer("\u274c У вас нет доступа к админ-панели.")
        return

    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        ["\ud83d\udcca Общая статистика", "\ud83d\udc65 Пользователи"],
        ["\ud83d\udcc1 Экспорт", "\u2699\ufe0f Настройки"]
    ])
    await message.answer("\ud83d\udd10 Admin Dashboard", reply_markup=kb)

# === MAIN ===
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))




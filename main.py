import os
import sqlite3
import re
from datetime import datetime, timedelta
from io import BytesIO

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode

from utils import generate_horizontal_chart

# ==== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ====

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN отсутстует в переменных окружения")
if not ADMIN_ID:
    raise RuntimeError("❌ ADMIN_ID отсутствует в переменных окружения")

# ==== ИНИЦИАЛИЗАЦИЯ ====

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ==== FSM ====

class DateRangeState(StatesGroup):
    start_date = State()
    end_date = State()

# ==== БАЗА ====

def connect_db():
    return sqlite3.connect("support_bot.db")

# ==== /start ====

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот аналитики по экзотическим животным 🦎\n\nИспользуй /exotic")

# ==== /exotic ====

@dp.message(Command("exotic"))
async def cmd_exotic(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="7 дней", callback_data="filter_7")
    kb.button(text="30 дней", callback_data="filter_30")
    kb.button(text="Год", callback_data="filter_365")
    kb.button(text="Произвольный период", callback_data="filter_custom")
    kb.adjust(1)
    await message.answer("Выбери период:", reply_markup=kb.as_markup())

# ==== Кнопка Произвольный период ====

@dp.callback_query(F.data == "filter_custom")
async def filter_custom(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите начальную дату в формате YYYY-MM-DD:")
    await state.set_state(DateRangeState.start_date)
    await callback.answer()

# ==== FSM: Ввод первой даты ====

@dp.message(DateRangeState.start_date)
async def set_start_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("\u2757 Неверный формат. Введите дату в формате YYYY-MM-DD:")
        return
    await state.update_data(start_date=date_text)
    await message.answer("Теперь введите конечную дату в формате YYYY-MM-DD:")
    await state.set_state(DateRangeState.end_date)

# ==== FSM: Ввод второй даты ====

@dp.message(DateRangeState.end_date)
async def set_end_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r"\d{4}-\d{2}-\d{2}", date_text):
        await message.answer("\u2757 Неверный формат. Введите дату в формате YYYY-MM-DD:")
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
        data = {animal: count for animal, count in rows}
        chart = generate_horizontal_chart(data, f"{start_date} - {end_date}")
        await message.answer_photo(types.InputFile(chart), caption=f"\ud83d\udcca Консультации с {start_date} по {end_date}")

    await state.clear()

# ==== Обработка фиксированных фильтров ====

async def process_filter(callback: CallbackQuery, days: int):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT animal_type, COUNT(*) FROM exotic_consultations
        WHERE consultation_date BETWEEN ? AND ?
        GROUP BY animal_type
    ''', (start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.message.answer("Нет данных за выбранный период.")
    else:
        data = {animal: count for animal, count in rows}
        chart = generate_horizontal_chart(data, f"Последние {days} дней")
        await callback.message.answer_photo(types.InputFile(chart), caption=f"\ud83d\udcca Консультации за {days} дней")

    await callback.answer()

@dp.callback_query(F.data == "filter_7")
async def filter_7(callback: CallbackQuery):
    await process_filter(callback, 7)

@dp.callback_query(F.data == "filter_30")
async def filter_30(callback: CallbackQuery):
    await process_filter(callback, 30)

@dp.callback_query(F.data == "filter_365")
async def filter_365(callback: CallbackQuery):
    await process_filter(callback, 365)

# ==== /admin ====

@dp.message(Command("admin"))
async def admin_command(message: Message):
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer("\u274c У вас нет доступа к админ-панели.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Общая статистика")],
            [KeyboardButton(text="Пользователи")],
            [KeyboardButton(text="Экспорт")],
            [KeyboardButton(text="Настройки")]
        ],
        resize_keyboard=True
    )
    await message.answer("\ud83d\udd10 Admin Dashboard", reply_markup=kb)

# ==== RUN ====

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))






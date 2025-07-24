import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils import (
    generate_horizontal_chart,
    generate_line_chart,
    generate_bar_chart,
    generate_pie_chart,
)
from exotic_analytics import (
    get_retention_stats,
    get_weekly_stats,
    get_summary_stats
)
from aiogram.types import FSInputFile

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN отсутствует в переменных окружения")
if not ADMIN_ID:
    raise RuntimeError("❌ ADMIN_ID отсутствует в переменных окружения")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

class DateRangeState(StatesGroup):
    start_date = State()
    end_date = State()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я бот аналитики по экзотическим животным 🦎\n\nИспользуй /exotic")

@dp.message(Command("exotic"))
async def exotic_handler(message: Message):
    stats = get_summary_stats()

    text = (
        "<b>📊 Аналитика по консультациям для экзотических животных:</b>\n\n"
        f"🔹 Всего консультаций: {stats['total']}\n"
        f"🔹 Уникальных пользователей: {stats['unique_users']}\n"
        f"🔹 Средняя длительность: {stats['avg_duration']} мин\n\n"
        "📅 <b>За последний месяц:</b>\n"
        f"🔹 Консультаций: {stats['monthly_count']}\n"
        f"🔹 Средняя длительность: {stats['monthly_avg_duration']} мин"
    )

    # Тестовые данные для графиков
    graph_data = {
        "Игуана": 21,
        "Паук-птицеед": 23,
        "Попугай": 38,
        "Фретка": 33,
        "Хамелеон": 35
    }

    bar_path = generate_bar_chart(graph_data)
    pie_path = generate_pie_chart(graph_data)

    await message.answer_photo(FSInputFile(bar_path))
    await message.answer(text, parse_mode="HTML")
    await message.answer_photo(FSInputFile(pie_path))

@dp.message(Command("admin"))
async def admin_dashboard(message: Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        await message.answer("🚫 У вас нет доступа к админ-панели.")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Общая статистика")],
            [KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="📤 Экспорт")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )

    await message.answer("🔐 Добро пожаловать в Admin Dashboard!", reply_markup=keyboard)

@dp.message(F.text == "📊 Общая статистика")
async def admin_stats(message: Message):
    total, repeat = get_retention_stats()
    await message.answer(f"📈 Общая статистика:\n– Всего консультаций: 134\n– Уникальных пользователей: {total}\n– Повторные визиты: {repeat}")

    weekly_data = get_weekly_stats()
    chart_path = generate_line_chart(weekly_data)
    await message.answer_photo(photo=FSInputFile(chart_path), caption="📉 Динамика по неделям")

@dp.message(F.text == "👥 Пользователи")
async def admin_users(message: Message):
    total, repeat = get_retention_stats()
    await message.answer(f"👤 Всего пользователей: {total}\n🔁 Повторные визиты: {repeat}")

@dp.message(F.text == "📤 Экспорт")
async def admin_export(message: Message):
    await message.answer("📤 Экспорт скоро будет доступен (CSV / Excel)")

@dp.message(F.text == "⚙️ Настройки")
async def admin_settings(message: Message):
    await message.answer("⚙️ Здесь будут настройки: смена периода, автоотчёты, фильтры и т.д.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

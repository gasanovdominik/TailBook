import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils import generate_horizontal_chart
from aiogram.types import FSInputFile

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

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

def get_period_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней", callback_data="period_7")],
        [InlineKeyboardButton(text="30 дней", callback_data="period_30")],
        [InlineKeyboardButton(text="Год", callback_data="period_365")],
        [InlineKeyboardButton(text="Произвольный период", callback_data="custom_period")]
    ])

@dp.message(Command("exotic"))
async def exotic_handler(message: Message):
    await message.answer("Выбери период:", reply_markup=get_period_keyboard())

@dp.callback_query()
async def handle_callback_query(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data.startswith("period_"):
        days = int(data.split("_")[1])
        end = datetime.now().date()
        start = end - timedelta(days=days)

        await callback.message.answer(f"📊 Анализ за период: {start} – {end}")

        test_data = {
            "Попугаи": 12,
            "Кошки": 30,
            "Собаки": 45,
            "Рептилии": 7,
            "Обезьяны": 2
        }
        image = generate_horizontal_chart(test_data)
        await callback.message.answer_photo(photo=image, caption="График консультаций по животным 🐾")

        await callback.answer()

    elif data == "custom_period":
        await state.set_state(DateRangeState.start_date)
        await callback.message.answer("Введите начальную дату в формате YYYY-MM-DD:")
        await callback.answer()

@dp.message(DateRangeState.start_date)
async def receive_start_date(message: Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(start_date=start_date)
        await state.set_state(DateRangeState.end_date)
        await message.answer("Введите конечную дату в формате YYYY-MM-DD:")
    except ValueError:
        await message.answer("❌ Неверный формат. Попробуйте снова: YYYY-MM-DD")

@dp.message(DateRangeState.end_date)
async def receive_end_date(message: Message, state: FSMContext):
    try:
        end_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        data = await state.get_data()
        start_date = data.get("start_date")
        await state.clear()
        await message.answer(f"📊 Анализ за период: {start_date} – {end_date}")
    except ValueError:
        await message.answer("❌ Неверный формат. Попробуйте снова: YYYY-MM-DD")

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
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел"
    )

    await message.answer("🔐 Добро пожаловать в Admin Dashboard!", reply_markup=keyboard)

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))









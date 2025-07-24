import os
import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# FSM состояния
class DateRangeState(StatesGroup):
    start_date = State()
    end_date = State()

# Бот и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Кнопки
filter_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="7 дней", callback_data="filter_7")],
    [InlineKeyboardButton(text="30 дней", callback_data="filter_30")],
    [InlineKeyboardButton(text="Год", callback_data="filter_365")],
    [InlineKeyboardButton(text="Произвольный период", callback_data="filter_custom")]
])

# Подключение к базе
def connect_db():
    return sqlite3.connect("support_bot.db")

# Команда /start
@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer("Привет! Я бот аналитики по экзотическим животным 🐍\n\nИспользуй /exotic")

# Команда /exotic
@dp.message(F.text == "/exotic")
async def exotic_handler(message: Message):
    await message.answer("Выбери период:", reply_markup=filter_keyboard)

# Команда /admin
@dp.message(F.text == "/admin")
async def admin_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещён.")
        return

    await message.answer("Admin Dashboard:\n\n(Здесь будут кнопки и функции админки)")

# Callback кнопки
@dp.callback_query(F.data.startswith("filter_"))
async def filter_callback(callback: CallbackQuery, state: FSMContext):
    period = callback.data.split("_")[1]
    now = datetime.now()

    if period == "custom":
        await callback.message.answer("Введите начальную дату в формате YYYY-MM-DD:")
        await state.set_state(DateRangeState.start_date)
        await callback.answer()
        return

    if period == "7":
        start = now - timedelta(days=7)
    elif period == "30":
        start = now - timedelta(days=30)
    elif period == "365":
        start = now - timedelta(days=365)
    else:
        await callback.message.answer("Неверный выбор.")
        return

    start_str = start.strftime("%Y-%m-%d 00:00:00")
    end_str = now.strftime("%Y-%m-%d 23:59:59")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT animal_type, COUNT(*) FROM exotic_consultations
        WHERE consultation_date BETWEEN ? AND ?
        GROUP BY animal_type
    ''', (start_str, end_str))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.message.answer("Нет данных за выбранный период.")
    else:
        text = f"Статистика консультаций:\n\n"
        for animal, count in rows:
            text += f"{animal}: {count}\n"
        await callback.message.answer(text)

    await callback.answer()

# Первая дата (ввод пользователем)
@dp.message(DateRangeState.start_date)
async def custom_start(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
        await state.update_data(start_date=text)
        await message.answer("Введите конечную дату в формате YYYY-MM-DD:")
        await state.set_state(DateRangeState.end_date)
    except ValueError:
        await message.answer("Неверный формат. Введите дату в формате YYYY-MM-DD.")

# Вторая дата
@dp.message(DateRangeState.end_date)
async def custom_end(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
        data = await state.get_data()
        start = data["start_date"]
        end = text

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT animal_type, COUNT(*) FROM exotic_consultations
            WHERE consultation_date BETWEEN ? AND ?
            GROUP BY animal_type
        ''', (start + " 00:00:00", end + " 23:59:59"))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await message.answer("Нет данных за выбранный период.")
        else:
            text = f"Статистика консультаций:\n\n"
            for animal, count in rows:
                text += f"{animal}: {count}\n"
            await message.answer(text)

        await state.clear()
    except ValueError:
        await message.answer("Неверный формат. Введите дату в формате YYYY-MM-DD.")

# Запуск
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))





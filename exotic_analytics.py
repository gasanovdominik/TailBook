import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import telebot

API_TOKEN = '7905050993:AAHV1XOtLoVwXfu--OJNTYlgnIzPoN9rG2w'
bot = telebot.TeleBot(API_TOKEN)

def connect_db():
    return sqlite3.connect('support_bot.db')

def consultations_summary():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM exotic_consultations")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM exotic_consultations")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(duration_minutes) FROM exotic_consultations")
    avg_time = cursor.fetchone()[0] or 0

    conn.close()

    return {
        'total_consultations': total,
        'unique_users': users,
        'avg_duration': round(avg_time, 1)
    }

def animal_type_chart():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''SELECT animal_type, COUNT(*) FROM exotic_consultations
                      GROUP BY animal_type''')
    data = cursor.fetchall()
    conn.close()

    types = [row[0] for row in data]
    counts = [row[1] for row in data]

    plt.figure(figsize=(8, 6))
    bars = plt.bar(types, counts, color='mediumseagreen')
    plt.title('Консультации по типу экзотических животных')
    plt.xlabel('Тип животного')
    plt.ylabel('Количество')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, int(yval), ha='center')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    return buf

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для аналитики консультаций экзотических животных 🦎\n\n"
        "Используй команду /exotic для получения статистики."
    )

@bot.message_handler(commands=['exotic'])
def send_exotic_analytics(message):
    summary = consultations_summary()
    img = animal_type_chart()

    caption = (
        f"📊 Аналитика по консультациям для экзотических животных:\n\n"
        f"🔹 Всего консультаций: {summary['total_consultations']}\n"
        f"🔹 Уникальных пользователей: {summary['unique_users']}\n"
        f"🔹 Средняя длительность: {summary['avg_duration']} мин\n"
    )

    bot.send_photo(message.chat.id, img, caption=caption)

bot.polling(none_stop=True)


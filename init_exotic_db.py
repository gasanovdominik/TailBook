import sqlite3
from datetime import datetime, timedelta
import random

def init_db():
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exotic_consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            animal_type TEXT NOT NULL,
            consultation_date TEXT NOT NULL,
            duration_minutes INTEGER
        )
    ''')

    exotic_animals = ['Игуана', 'Хамелеон', 'Фретка', 'Попугай', 'Паук-птицеед']
    now = datetime.now()

    for _ in range(50):
        user_id = random.randint(1000, 1020)
        animal = random.choice(exotic_animals)
        date = now - timedelta(days=random.randint(0, 60))
        duration = random.randint(10, 60)

        cursor.execute('''
            INSERT INTO exotic_consultations (user_id, animal_type, consultation_date, duration_minutes)
            VALUES (?, ?, ?, ?)
        ''', (user_id, animal, date.strftime('%Y-%m-%d %H:%M:%S'), duration))

    conn.commit()
    conn.close()
    print("База данных инициализирована.")

if __name__ == "__main__":
    init_db()

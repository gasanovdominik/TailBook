import sqlite3
from datetime import datetime, timedelta

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


def last_month_stats():
    conn = connect_db()
    cursor = conn.cursor()

    last_month = datetime.now() - timedelta(days=30)
    last_month_str = last_month.strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        SELECT COUNT(*), AVG(duration_minutes)
        FROM exotic_consultations
        WHERE consultation_date >= ?
    ''', (last_month_str,))
    count, avg = cursor.fetchone()
    conn.close()

    return {
        'count': count or 0,
        'avg_duration': round(avg or 0, 1)
    }


def animal_counts_by_type():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT animal_type, COUNT(*) FROM exotic_consultations
        GROUP BY animal_type
    ''')
    data = cursor.fetchall()
    conn.close()

    return {row[0]: row[1] for row in data}

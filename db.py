import sqlite3
from config import db_path

def get_connection():
    return sqlite3.connect(db_path)


def add_user(username, user_id):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("""
            INSERT INTO users (username, user_id) 
            VALUES (?, ?)
            ON CONFLICT (user_id) DO NOTHING
        """, (username, user_id))


def add_user_info(user_id, section, value):
    with get_connection() as con:
        cursor = con.cursor()
        query = f"UPDATE users SET {section} = ? WHERE user_id = ?"
        cursor.execute(query, (value, user_id))


def check_if_user_filled(user_id):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT filled FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
    return res and res[0]


def select_all_user_data(user_id):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT 
                username, 
                user_id,
                name,
                phone, 
                area, 
                wanted_work, 
                with_car, 
                is_active 
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        res = cursor.fetchone()
    return res


def select_user_field(user_id, field):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(f"""
            SELECT 
                {field}
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        res = cursor.fetchone()
    return res[0]


def check_queue():
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT id, user_id, action, sheet_name FROM queue ORDER BY id LIMIT 1")
        res = cursor.fetchone()
    return res


def delete_queue(queue_id):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("DELETE FROM queue WHERE id = ?", (queue_id,))


def add_queue(user_id, action, sheet_name):
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("""
            INSERT INTO queue (user_id, action, sheet_name) 
            VALUES (?, ?, ?)
        """, (user_id, action, sheet_name))


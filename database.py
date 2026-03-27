import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pflf.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_transaction(tx):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO transactions (id, data) VALUES (?, ?)",
        (tx['id'], json.dumps(tx))
    )
    conn.commit()
    conn.close()


def get_recent_transactions(limit=500):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT data FROM transactions ORDER BY rowid DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [json.loads(row[0]) for row in rows]


def save_stats(stats_dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO stats (key, data) VALUES ('app_stats', ?)",
        (json.dumps(stats_dict),)
    )
    conn.commit()
    conn.close()


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM stats WHERE key='app_stats'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

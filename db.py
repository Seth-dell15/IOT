import sqlite3

conn = sqlite3.connect("serrure.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cartes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT UNIQUE,
        role TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS serrures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT UNIQUE,
        nom TEXT,
        roles_autorises TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT UNIQUE
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid_carte TEXT,
        uid_serrure TEXT,
        role TEXT,
        action TEXT,
        date_utilisation DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()

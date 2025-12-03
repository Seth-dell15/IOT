import sqlite3

DB_PATH = "serrure.db"

# Connexion globale
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

def init_db():
    # Table cartes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cartes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT UNIQUE,
        role TEXT
    )
    """)

    # Table serrures
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS serrures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT UNIQUE,
        nom TEXT,
        roles_autorises TEXT
    )
    """)

    # Table roles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT UNIQUE
    )
    """)

    # Table logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid_carte TEXT,
        uid_serrure TEXT,
        role TEXT,
        action TEXT,
        date_utilisation DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()


def get_conn():
    """Retourne la connexion SQLite"""
    return conn


def get_cursor():
    """Retourne le curseur global"""
    return cursor

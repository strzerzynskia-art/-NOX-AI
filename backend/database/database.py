import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "nox_ai.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialiser_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age TEXT,
                appearance TEXT,
                personality TEXT,
                backstory TEXT,
                scenario TEXT,
                first_message TEXT
            )
        """)


def sauvegarder_personnage(personnage):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO characters (
                name, age, appearance, personality,
                backstory, scenario, first_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            personnage.name,
            personnage.age,
            personnage.appearance,
            personnage.personality,
            personnage.backstory,
            personnage.scenario,
            personnage.first_message
        ))

        return cursor.lastrowid


def recuperer_personnages():
    with get_connection() as connection:
        result = connection.execute(
            "SELECT * FROM characters ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in result]

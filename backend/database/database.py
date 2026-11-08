import json
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "nox_ai.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialiser_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age TEXT,
                appearance TEXT DEFAULT '',
                personality TEXT DEFAULT '',
                backstory TEXT DEFAULT '',
                scenario TEXT DEFAULT '',
                first_message TEXT DEFAULT '',
                avatar TEXT DEFAULT '',
                personality_tags TEXT DEFAULT '[]',
                secrets TEXT DEFAULT '',
                relationships TEXT DEFAULT '',
                complex_relationships INTEGER DEFAULT 1,
                evolving_personality INTEGER DEFAULT 1,
                enhanced_memory INTEGER DEFAULT 1,
                theme TEXT DEFAULT 'cyber',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        existing = {row["name"] for row in connection.execute("PRAGMA table_info(characters)")}
        additions = {
            "avatar": "TEXT DEFAULT ''",
            "personality_tags": "TEXT DEFAULT '[]'",
            "secrets": "TEXT DEFAULT ''",
            "relationships": "TEXT DEFAULT ''",
            "complex_relationships": "INTEGER DEFAULT 1",
            "evolving_personality": "INTEGER DEFAULT 1",
            "enhanced_memory": "INTEGER DEFAULT 1",
            "theme": "TEXT DEFAULT 'cyber'",
            "created_at": "TEXT"
        }
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(f"ALTER TABLE characters ADD COLUMN {column} {definition}")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                memory_type TEXT DEFAULT 'event',
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
            )
        """)


def _character_dict(row):
    data = dict(row)
    try:
        data["personality_tags"] = json.loads(data.get("personality_tags") or "[]")
    except (ValueError, TypeError):
        data["personality_tags"] = []
    for key in ("complex_relationships", "evolving_personality", "enhanced_memory"):
        data[key] = bool(data.get(key, 1))
    return data


def sauvegarder_personnage(personnage):
    data = personnage.model_dump() if hasattr(personnage, "model_dump") else personnage.dict()
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO characters (
                name, age, appearance, personality, backstory, scenario,
                first_message, avatar, personality_tags, secrets, relationships,
                complex_relationships, evolving_personality, enhanced_memory, theme
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["name"], data.get("age"), data.get("appearance", ""),
            data.get("personality", ""), data.get("backstory", ""),
            data.get("scenario", ""), data.get("first_message", ""),
            data.get("avatar", ""), json.dumps(data.get("personality_tags", []), ensure_ascii=False),
            data.get("secrets", ""), data.get("relationships", ""),
            int(data.get("complex_relationships", True)),
            int(data.get("evolving_personality", True)),
            int(data.get("enhanced_memory", True)), data.get("theme", "cyber")
        ))
        return cursor.lastrowid


def recuperer_personnages():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM characters ORDER BY id DESC").fetchall()
        return [_character_dict(row) for row in rows]


def recuperer_personnage(character_id):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
        return _character_dict(row) if row else None


def sauvegarder_message(character_id, role, content):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO messages (character_id, role, content) VALUES (?, ?, ?)",
            (character_id, role, content)
        )
        return cursor.lastrowid


def recuperer_messages(character_id, limit=60):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, role, content, created_at FROM messages WHERE character_id = ? ORDER BY id DESC LIMIT ?",
            (character_id, limit)
        ).fetchall()
        return [dict(row) for row in reversed(rows)]


def sauvegarder_memoire(character_id, content, memory_type="event"):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO memories (character_id, memory_type, content) VALUES (?, ?, ?)",
            (character_id, memory_type, content)
        )
        return cursor.lastrowid


def recuperer_memoires(character_id, limit=30):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, memory_type, content, created_at FROM memories WHERE character_id = ? ORDER BY id DESC LIMIT ?",
            (character_id, limit)
        ).fetchall()
        return [dict(row) for row in reversed(rows)]

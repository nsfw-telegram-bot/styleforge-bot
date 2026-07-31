import aiosqlite
from datetime import datetime

DB_PATH = "styles.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS styles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                image_path TEXT,
                style_description TEXT,
                created_at TEXT
            )
        """)
        await db.commit()

async def add_style(user_id: int, name: str, image_path: str, description: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO styles (user_id, name, image_path, style_description, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, image_path, description, datetime.now().isoformat())
        )
        await db.commit()

async def get_user_styles(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, image_path, style_description, created_at FROM styles WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        return await cursor.fetchall()

async def get_style_by_id(style_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM styles WHERE id = ? AND user_id = ?",
            (style_id, user_id)
        )
        return await cursor.fetchone()

async def delete_style(style_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM styles WHERE id = ? AND user_id = ?", (style_id, user_id))
        await db.commit()
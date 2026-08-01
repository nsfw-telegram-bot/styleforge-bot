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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS balances (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
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

async def get_balance(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT balance FROM balances WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

async def add_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO balances (user_id, balance) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
        """, (user_id, amount, amount))
        await db.commit()

async def deduct_balance(user_id: int, amount: int) -> bool:
    current = await get_balance(user_id)
    if current < amount:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE balances SET balance = balance - ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()
    return True

async def add_deposit_record(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO deposits (user_id, amount, created_at) VALUES (?, ?, ?)",
            (user_id, amount, datetime.now().isoformat())
        )
        await db.commit()

async def get_user_deposits(user_id: int, limit: int = 15):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT amount, created_at FROM deposits WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return await cursor.fetchall()

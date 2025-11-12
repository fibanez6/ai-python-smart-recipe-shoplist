import aiosqlite
import json
import time
import os
from typing import Optional

class CacheAgent:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv('CACHE_DB', './data/cache.db')
        self._inited = False

    async def _ensure(self):
        if self._inited:
            return
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                expires_at INTEGER
            )
            ''')
            await db.commit()
        self._inited = True

    def make_key(self, ingredient) -> str:
        name = ingredient.name if hasattr(ingredient, 'name') else ingredient.get('name')
        qty = getattr(ingredient, 'qty', '') or ''
        unit = getattr(ingredient, 'unit', '') or ''
        return f"{name.lower()}|{qty}|{unit}"

    async def get(self, key: str):
        await self._ensure()
        now = int(time.time())
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute('SELECT value, expires_at FROM cache WHERE key=?', (key,))
            row = await cur.fetchone()
            await cur.close()
            if not row:
                return None
            value, expires_at = row
            if expires_at and expires_at < now:
                async with aiosqlite.connect(self.db_path) as db2:
                    await db2.execute('DELETE FROM cache WHERE key=?', (key,))
                    await db2.commit()
                return None
            return json.loads(value)

    async def set(self, key: str, value, ttl_seconds: int = 24*3600):
        await self._ensure()
        expires_at = int(time.time()) + ttl_seconds if ttl_seconds else None
        js = json.dumps(value, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)', (key, js, expires_at))
            await db.commit()
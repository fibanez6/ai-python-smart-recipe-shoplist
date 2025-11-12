
import duckdb
import json

class CacheDB:
    def __init__(self, db_path='data/cache.db'):
        self.conn = duckdb.connect(db_path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS cache (url TEXT PRIMARY KEY, data TEXT)")

    def save_recipe(self, url, data):
        self.conn.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?)",
            [url, json.dumps(data)]
        )

    def get_recipe(self, url):
        result = self.conn.execute("SELECT data FROM cache WHERE url=?", [url]).fetchone()
        return json.loads(result[0]) if result else None

import hashlib
import logging
import os
import sys
import time
from typing import Optional
import pickle

from unqlite import UnQLite

from app.config.pydantic_config import DB_MANAGER_SETTINGS
from app.utils.str_helpers import object_to_str

from ..config.logging_config import get_logger, log_function_call

logger = get_logger(__name__)

#  Original / source content
SOURCE_ALIAS="source"
PROCESSED_ALIAS = "processed"

class DBManager:
    def __init__(self, db_path: str = DB_MANAGER_SETTINGS.path):
        self.name = "DBManager"
        self.db = UnQLite(db_path)
        self.enabled = DB_MANAGER_SETTINGS.enabled

        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

        if self.enabled:
            logger.info(f"[{self.name}] Using database at: {db_path}")
        else:
            logger.warning(f"[{self.name}] Database is disabled")

    def _get_hash(self, key: str, alias: str) -> str:
        """Generate a hash for the key and alias to use as key."""
        return hashlib.md5(f"{alias}_{key}".encode()).hexdigest()

    def save(self, key: str, obj: any, alias: str = None, format: str = "json", **kwargs) -> None:
        """Save an object in the database under the given key."""

        if not self.enabled:
            return None

        try: 
            obj_str = object_to_str(obj)
            obj_size = sys.getsizeof(obj_str)

            log_function_call("DBManager.save", {
                    "cache_key": key,
                    "alias": alias,
                    "format": format,
                    "data_size": f"{obj_size} bytes ({obj_size/1024:.2f} KB)",
                    "data_preview": obj_str[:20] + ("..." if len(obj_str) > 20 else "")
                })
            
            load_from = kwargs.get('data_from', None)
            if load_from == "local_db":
                logger.debug(f"[{self.name}] Skipping save since data loaded from local db")
                return None
            
            hash_key = self._get_hash(key, alias or SOURCE_ALIAS)
            db_entry = {
                    "hash_key": hash_key,
                    "alias": alias,
                    "timestamp": time.time(),
                    "data_size": f"{obj_size} bytes ({obj_size/1024:.2f} KB)",
                    "data_format": format,
                    "data": obj
                }

            self.db[hash_key] = pickle.dumps(db_entry)

            self.db.commit()
            logger.debug(f"[{self.name}] Saved obj to db for {hash_key} and alias '{alias}'")
        except Exception as e:
            logger.error(f"[{self.name}] Error saving to database: {e}")
            return None

    def load(self, key: str, alias: str = None) -> Optional[dict]:
        """Retrieve an object from the database by key."""

        if not self.enabled:
            return None
        
        try:
            hash_key = self._get_hash(key, alias or SOURCE_ALIAS)

            if self.exists(hash_key) is False:
                logger.debug(f"[{self.name}] DB miss for key: {hash_key} (alias='{alias}')")
                return None

            obj_bytes = self.db[hash_key]
            obj_dict = pickle.loads(obj_bytes)
            obj_dict["data_from"] = "local_db"

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[{self.name}] Loaded obj from db for {hash_key} and alias '{alias}': {obj_dict}")

            logger.info(f"[{self.name}] DB hit for key: {hash_key} (alias='{alias}')")
            return obj_dict
        except KeyError as e:
            logger.error(f"[{self.name}] Error loading from cache: {e}")
            return None
        
    def delete(self, key: str) -> bool:
        """Delete an object from the database by key."""
        if key in self.db:
            del self.db[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if an object exists in the database by key."""
        return key in self.db
    
    def all_keys(self) -> list[str]:
        """Get all keys in the specified collection."""
        return list(self.db.keys())
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when exiting the 'with' block.
        Ensures the database is properly closed.
        """
        if self.db:
            self.db.close()
    
# Global cache instance
_db_instance = None

def get_db_manager() -> DBManager:
    """Get or create the global cache manager instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DBManager()
    return _db_instance
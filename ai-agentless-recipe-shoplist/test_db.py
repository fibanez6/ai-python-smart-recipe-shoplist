from anyio import sleep
from unqlite import UnQLite
import rich
import pickle

from app.storage.db_manager import get_db_manager

rich.print("\n--- Using Key-Value mode (no collection) ---")


# with UnQLite('/tmp/ai_shopping/db/test.db') as db:
#     # Set the data
#     db['config:theme'] = 'dark'
#     db['user:last_login'] = '2025-11-12'
#     db['app:status'] = 'running'
#     db['config:retries'] = 3
#     db['hashhh'] = {
#         "field1": "value1",
#         "field2": 42,
#         "field3": [1, 2, 3]
#     }

# with UnQLite('/tmp/ai_shopping/db/test.db') as db:
#     rich.print("-" * 43)

#     # Get all data
#     for key,val in db:
#         rich.print(f"Key: {key} => Value: {val}")
    
#     rich.print(f"Total entries in DB: {len(db)}\n")


# with UnQLite('/tmp/ai_shopping/db/shoplist.db') as db:
#     rich.print("-" * 43)

#     # Get all data
#     for key,val in db:
#         rich.print(f"Key: {key} => Value: {val}")
    
#     rich.print(f"Total entries in DB: {len(db)}\n")



with UnQLite('/tmp/ai_shopping/db/shoplist.db') as db:
    hash_key='ec6fd0719967fad5f1f65a2824692321'
    obj_bytes = db[hash_key]
    obj_dict = pickle.loads(obj_bytes)

    rich.print(f"\nLoaded data for '{hash_key}': {obj_dict}\n")

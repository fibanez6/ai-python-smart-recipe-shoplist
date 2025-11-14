from anyio import sleep
from unqlite import UnQLite
import rich
import pickle

from app.storage.db_manager import get_db_manager
from app.utils.str_helpers import object_to_str

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
#         obj_dict = pickle.loads(val)
#         obj_str = object_to_str(obj_dict)
#         rich.print(f"Key: {key} => Value: {obj_str[:500]}...")  # Print first 200 chars
    
#     rich.print(f"Total entries in DB: {len(db)}\n")



with UnQLite('/tmp/ai_shopping/db/shoplist.db') as db:
    hash_key='1bef6a57a4f2aaa9acd48a31237a9cc8'
    obj_bytes = db[hash_key]
    obj_dict = pickle.loads(obj_bytes)

    rich.print(f"\nLoaded data for '{hash_key}': {obj_dict}\n")

    # del db[hash_key]
    # rich.print(f"Deleted key '{hash_key}' from the database.")

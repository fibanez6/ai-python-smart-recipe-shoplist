"""Content storage for saving and loading web content to/from disk."""

import hashlib
import json
import time
from pathlib import Path

from ..config.logging_config import get_logger, log_function_call
from ..config.pydantic_config import STORAGE_SETTINGS

logger = get_logger(__name__)

#  Original / source content
SOURCE_ALIAS="source"
PROCESSED_ALIAS = "processed"

DATA = "data"
LOADED_FROM_DISK = {"data_from": "Local_disk"}

class StorageManager:
    """Manages saving and loading of web content to/from disk files."""

    def __init__(self, tmp_folder: Path = STORAGE_SETTINGS.tmp_folder):
        """
        Initialize the content storage.
        
        Args:
            tmp_folder: Base temporary folder for storage
        """
        self.name = "StorageManager"
        self.tmp_folder = tmp_folder
        self.enable_saving = STORAGE_SETTINGS.enable_saving
        self.enable_loading = STORAGE_SETTINGS.enable_loading

        # Content folder inside tmp folder
        self.content_folder = self.tmp_folder / "content"
        
        # Create content folder if needed and saving is enabled
        if self.enable_saving:
            self.content_folder.mkdir(parents=True, exist_ok=True)

        logger.debug(f"[{self.name}] Initialized - Saving: {self.enable_saving}, Loading: {self.enable_loading}")
        logger.debug(f"[{self.name}] Content folder: {self.content_folder}")

    def _get_url_hash(self, url: str, alias: str) -> str:
        """Generate a hash for the URL to use as filename base."""
        return hashlib.md5(f"{alias}:{url}".encode()).hexdigest()

    def save(self, url: str, data: str, alias: str = SOURCE_ALIAS, format: str = "txt") -> dict[str, str]:
        """
        Save the data to disk.

        Args:
            url: URL of the data
            data: Data to save
            alias: Alias to differentiate types of content (e.g., "original", "processed")
            format: Format of the data (e.g., "html", "txt")

        Returns:
            dict with file path of saved data (empty if saving disabled)
        """
        if not self.enable_saving:
            logger.debug(f"[{self.name}] Content saving disabled for {url}")
            return {}

        log_function_call("StorageManager.save", {
            "url": url,
            "data_preview": str(data)[:20] + "...",
            "alias": alias,
            "format": format,
            "path": str(self.content_folder)
        })

        url_hash = self._get_url_hash(url, alias)
        file_path = self.content_folder / url_hash
        mapping_path = self.content_folder / f"{url_hash}_mapping.json"

        metadata = {
            "url": url,
            "alias": alias,
            "hash": url_hash,
            "timestamp": time.time(),
            "file": str(file_path),
            "data_size": len(data),
            "data_format": format
        }

        try:
            # Prepare data for writing based on format
            if format == "json" or format == "dict" or isinstance(data, dict):
                to_write = json.dumps(data, ensure_ascii=False, indent=2)
                metadata["data_format"] = "json"
            else:
                to_write = data

            # Write the content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(to_write)
            logger.debug(f"[{self.name}] Saved content to file: {file_path}")

            # Write the metadata mapping file
            with open(mapping_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            metadata["url_mapping_file"] = str(mapping_path)

            logger.info(f"[{self.name}] Saved content file for {url} (hash: {url_hash})")
        except IOError as e:
            logger.warning(f"[{self.name}] Error saving content to disk for {url}: {e}")
            return {}

        return metadata

    def load(self, url: str, alias: str = SOURCE_ALIAS) -> dict[str, str]:
        """
        Load data from disk for the given URL.

        Args:
            url: URL of the content
            alias: Alias to differentiate types of data (e.g., "original", "processed")

        Returns:
            dict with content data loaded from disk (empty if not found or loading disabled)
        """
        if not self.enable_loading:
            logger.debug(f"[{self.name}] Content loading disabled for {url}")
            return {}

        log_function_call("StorageManager.load", {
            "url": url,
            "alias": alias,
            "path": str(self.content_folder)
        })

        if not self.content_folder.exists():
            logger.debug(f"[{self.name}] Content folder does not exist.")
            return {}

        url_hash = self._get_url_hash(url, alias)
        mapping_file = self.content_folder / f"{url_hash}_mapping.json"

        if not mapping_file.exists():
            logger.warning(f"[{self.name}] No URL mapping file found on disk for {url} (hash: {url_hash})")
            return {}

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except IOError as e:
            logger.warning(f"[{self.name}] Error reading mapping file for {url}: {e}")
            return {}

        file_path = Path(metadata.get("file")) if metadata.get("file") else None
        if not file_path.exists():
            logger.debug(f"[{self.name}] No content file found on disk for {url} (hash: {url_hash})")
            return {}

        try:
            type_format = metadata.get("data_format", "txt")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f) if type_format == "json" else f.read()

            logger.info(f"[{self.name}] Loaded {type_format} data from disk for {url} (hash: {url_hash})")
            logger.debug(f"[{self.name}] Loaded data from file: {file_path}")
            metadata.update(LOADED_FROM_DISK)
            metadata["data"] = data
        except IOError as e:
            logger.warning(f"[{self.name}] Error reading content file for {url}: {e}")
            return {}

        return metadata

    def clear(self) -> int:
        """
        Remove all files in the content folder.

        Returns:
            Number of files removed.
        """
        removed_files = 0

        if not self.content_folder.exists():
            logger.info(f"[{self.name}] Content folder does not exist, nothing to clear.")
            return removed_files

        for content_file in self.content_folder.iterdir():
            try:
                content_file.unlink()
                removed_files += 1
            except OSError as e:
                logger.warning(f"[{self.name}] Failed to remove file {content_file}: {e}")

        # Attempt to remove the folder if empty
        try:
            self.content_folder.rmdir()
        except OSError:
            pass  # Folder not empty or cannot be removed

        logger.info(f"[{self.name}] Removed {removed_files} content files")
        return removed_files
    
    def get_stats(self) -> dict[str, any]:
        """Get content storage statistics."""
        content_files_count = 0
        content_files_size = 0
        
        if self.content_folder.exists():
            for content_file in self.content_folder.iterdir():
                try:
                    content_files_count += 1
                    content_files_size += content_file.stat().st_size
                except OSError:
                    pass  # Skip files that can't be accessed
        
        return {
            "entries": content_files_count,
            "total_size": content_files_size,
            "folder": str(self.content_folder) if self.content_folder.exists() else "N/A",
            "saving_enabled": self.enable_saving,
            "loading_enabled": self.enable_loading
        }

# Global storage instance
_storage_instance = None

def get_storage_manager(path: Path = None) -> StorageManager:
    """Get or create the global content storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageManager(path) if path else StorageManager()
    return _storage_instance
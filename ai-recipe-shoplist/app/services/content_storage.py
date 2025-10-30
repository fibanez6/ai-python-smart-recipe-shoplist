"""Content storage for saving and loading web content to/from disk."""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict

from ..config.logging_config import get_logger, log_function_call
from ..config.pydantic_config import STORAGE_SETTINGS

logger = get_logger(__name__)

ORIGINAL_CONTENT = "content"
CLEANED_CONTENT = "cleaned_content"
CLEANED_CONTENT_FORMAT = "cleaned_content_format"
LOADED_ORIGINAL_CONTENT = "loaded_content_from_disk"
LOADED_CLEANED_CONTENT = "loaded_cleaned_content_from_disk"
URL_MAPPING = "url_mapping"

class ContentStorage:
    """Manages saving and loading of web content to/from disk files."""

    def __init__(self, tmp_folder: Path = STORAGE_SETTINGS.tmp_folder):
        """
        Initialize the content storage.
        
        Args:
            tmp_folder: Base temporary folder for storage
        """
        self.name = "ContentStorage"
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

    def _get_url_hash(self, url: str) -> str:
        """Generate a hash for the URL to use as filename base."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def save_fetch_content(self, url: str, fetch_content: Dict[str, str]) -> Dict[str, str]:
        """
        Save both original and cleaned content to separate files on disk.

        Args:
            url: URL of the content
            fetch_content: Dict containing original and optionally cleaned HTML content.
            - "content": Original HTML content (required)
            - "cleaned_content": Cleaned HTML content (optional)
            - "loaded_content_from_disk": True if loaded from disk (optional)
            - "loaded_cleaned_content_from_disk": True if cleaned content loaded from disk (optional)

        Returns:
            Dict with file paths of saved content (empty if saving disabled)
        """
        if not self.enable_saving:
            logger.debug(f"[{self.name}] Content saving disabled for {url}")
            return {}
        
        log_function_call("ContentStorage.save_fetch_content", {
            "url": url,
            "fetch_content": str(fetch_content)[:20] + "...",
            "loaded_original_content": fetch_content.get(LOADED_ORIGINAL_CONTENT, False),
            "loaded_cleaned_content": fetch_content.get(LOADED_CLEANED_CONTENT, False),
        })

        url_hash = self._get_url_hash(url)        
        saved_files = {}
        
        try:
            if ORIGINAL_CONTENT not in fetch_content:
                raise ValueError("Original content is missing")

            # Save original content if it is not loaded from disk
            if not fetch_content.get(LOADED_ORIGINAL_CONTENT, False):
                original_file = self.content_folder / f"{url_hash}_original.html"
                with open(original_file, 'w', encoding='utf-8') as f:
                    f.write(fetch_content[ORIGINAL_CONTENT])
                saved_files["original_file"] = str(original_file)
                logger.debug(f"[{self.name}] Saved original content to: {original_file}")
            else:
                logger.debug(f"[{self.name}] No original content to save for: {url}")
            
            # Save cleaned content if provided and not loaded from disk
            cleaned_content_format = "html"
            if CLEANED_CONTENT in fetch_content and not fetch_content.get(LOADED_CLEANED_CONTENT, False):
                cleaned_content = fetch_content[CLEANED_CONTENT]
                cleaned_file = self.content_folder / f"{url_hash}_cleaned.html"

                # Check if cleaned_content is a list or dict (JSON-like)
                if isinstance(cleaned_content, (list, dict)):
                    cleaned_content = json.dumps(cleaned_content, ensure_ascii=False, indent=2)
                    cleaned_file = self.content_folder / f"{url_hash}_cleaned.json"
                    cleaned_content_format = "json"

                with open(cleaned_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)

                saved_files["cleaned_file"] = str(cleaned_file)
                logger.debug(f"[{self.name}] Saved cleaned content to: {cleaned_file}")
            else:
                logger.debug(f"[{self.name}] No cleaned content to save for: {url}")

            # Save URL mapping for reference
            if not fetch_content.get(LOADED_ORIGINAL_CONTENT, False):
                url_mapping_file = self.content_folder / f"{url_hash}_url.txt"
                with open(url_mapping_file, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {url}\n")
                    f.write(f"Hash: {url_hash}\n")
                    f.write(f"Timestamp: {time.time()}\n")
                    f.write(f"Original file: {saved_files.get('original_file', 'N/A')}\n")
                    f.write(f"Cleaned file: {saved_files.get('cleaned_file', 'N/A')}\n")
                    f.write(f"Cleaned file format: {cleaned_content_format}\n")
                saved_files["url_mapping_file"] = str(url_mapping_file)

                logger.info(f"[{self.name}] Saved content files for {url} (hash: {url_hash})")
            else:
                logger.info(f"[{self.name}] Skipped saving content files for {url} (already loaded from disk)")

        except IOError as e:
            logger.warning(f"[{self.name}] Error saving content to disk for {url}: {e}")

        return saved_files
    
    def load_html_content(self, url: str) -> Dict[str, str]:
        """
        Load both original and cleaned content from disk if available.
        
        Args:
            url: URL of the content
            
        Returns:
            Dict with content loaded from disk (empty if not found or loading disabled)
        """
        if not self.enable_loading:
            logger.debug(f"[{self.name}] Content loading disabled for {url}")
            return {}
        
        if not self.content_folder.exists():
            return {}
        
        url_hash = self._get_url_hash(url)
        loaded_content = {}
        
        try:
            # Load original content
            original_file = self.content_folder / f"{url_hash}_original.html"
            if original_file.exists():
                with open(original_file, 'r', encoding='utf-8') as f:
                    loaded_content[ORIGINAL_CONTENT] = f.read()
                loaded_content[LOADED_ORIGINAL_CONTENT] = True
                logger.debug(f"[{self.name}] Loaded original content from: {original_file}")
            
            # Load cleaned content
            cleaned_file_html = self.content_folder / f"{url_hash}_cleaned.html"
            if cleaned_file_html.exists():
                with open(cleaned_file_html, 'r', encoding='utf-8') as f:
                    loaded_content[CLEANED_CONTENT] = f.read()
                loaded_content[LOADED_CLEANED_CONTENT] = True
                loaded_content[CLEANED_CONTENT_FORMAT] = "html"
                logger.debug(f"[{self.name}] Loaded cleaned content from: {cleaned_file_html}")

            # Load cleaned content (JSON)
            cleaned_file_json = self.content_folder / f"{url_hash}_cleaned.json"
            if cleaned_file_json.exists():
                with open(cleaned_file_json, 'r', encoding='utf-8') as f:
                    loaded_content[CLEANED_CONTENT] = json.load(f)
                loaded_content[LOADED_CLEANED_CONTENT] = True
                loaded_content[CLEANED_CONTENT_FORMAT] = "json"
                logger.debug(f"[{self.name}] Loaded cleaned content from: {cleaned_file_json}")

            # Load URL mapping
            url_mapping_file = self.content_folder / f"{url_hash}_url.txt"
            if url_mapping_file.exists():
                with open(url_mapping_file, 'r', encoding='utf-8') as f:
                    loaded_content[URL_MAPPING] = f.read()
            
            if loaded_content:
                logger.info(f"[{self.name}] Loaded content from disk for {url} (hash: {url_hash})")
            else:
                logger.debug(f"[{self.name}] No content files found on disk for {url} (hash: {url_hash})")

        except IOError as e:
            logger.warning(f"[{self.name}] Error loading content from disk for {url}: {e}")

        return loaded_content
    
    def has_cleaned_content(self, url: str) -> bool:
        """
        Check if cleaned content exists on disk for the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if cleaned content file exists, False otherwise
        """
        if not self.enable_loading or not self.content_folder.exists():
            return False
        
        url_hash = self._get_url_hash(url)
        cleaned_file = self.content_folder / f"{url_hash}_cleaned.html"
        return cleaned_file.exists()
    
    def clear_content_files(self) -> int:
        """
        Clear all saved content files.
        
        Returns:
            Number of files cleared
        """
        content_files_count = 0
        
        if self.content_folder.exists():
            for content_file in self.content_folder.iterdir():
                try:
                    content_file.unlink()
                    content_files_count += 1
                except OSError as e:
                    logger.warning(f"[{self.name}] Error removing content file {content_file}: {e}")
            
            # Remove empty content folder
            try:
                self.content_folder.rmdir()
            except OSError:
                pass  # Folder might not be empty
        
        logger.info(f"[{self.name}] Cleared {content_files_count} content files")
        return content_files_count
    
    def get_content_stats(self) -> Dict[str, any]:
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
    
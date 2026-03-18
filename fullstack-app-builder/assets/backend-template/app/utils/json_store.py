"""
Thread-safe JSON file storage with CRUD operations.
Each entity gets its own JSON file in the storage/ directory.
"""
import json
import os
import uuid
import shutil
from datetime import datetime, timezone
from threading import Lock
from typing import Optional


class JsonStore:
    """File-based JSON storage with thread-safe CRUD operations."""

    def __init__(self, entity_name: str, storage_dir: str = "storage", seed_dir: str = "../data"):
        self.entity_name = entity_name
        self.storage_dir = storage_dir
        self.seed_dir = seed_dir
        self.file_path = os.path.join(storage_dir, f"{entity_name}.json")
        self._lock = Lock()
        os.makedirs(storage_dir, exist_ok=True)
        self._seed_if_empty()

    def _seed_if_empty(self):
        """Copy seed data from data/ to storage/ on first run."""
        if not os.path.exists(self.file_path):
            seed_file = os.path.join(self.seed_dir, f"{self.entity_name}.json")
            if os.path.exists(seed_file):
                shutil.copy2(seed_file, self.file_path)
            else:
                self._write([])

    def _read(self) -> list[dict]:
        with self._lock:
            if not os.path.exists(self.file_path):
                return []
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write(self, data: list[dict]):
        with self._lock:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all(self, filters: Optional[dict] = None) -> list[dict]:
        """Return all records, optionally filtered by field values."""
        items = self._read()
        if filters:
            for key, value in filters.items():
                if value is not None:
                    items = [
                        item for item in items
                        if str(item.get(key, "")).lower().find(str(value).lower()) != -1
                    ]
        return items

    def get_by_id(self, item_id: str) -> Optional[dict]:
        """Return a single record by ID, or None."""
        items = self._read()
        for item in items:
            if item.get("id") == item_id:
                return item
        return None

    def create(self, data: dict) -> dict:
        """Create a new record with auto-generated ID and timestamps."""
        items = self._read()
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": str(uuid.uuid4()),
            **data,
            "created_at": now,
            "updated_at": now,
        }
        items.append(record)
        self._write(items)
        return record

    def update(self, item_id: str, data: dict) -> Optional[dict]:
        """Update fields on an existing record. Returns updated record or None."""
        items = self._read()
        for i, item in enumerate(items):
            if item.get("id") == item_id:
                now = datetime.now(timezone.utc).isoformat()
                # Only update fields that are provided and not None
                update_data = {k: v for k, v in data.items() if v is not None}
                items[i] = {**item, **update_data, "updated_at": now}
                self._write(items)
                return items[i]
        return None

    def delete(self, item_id: str) -> bool:
        """Delete a record by ID. Returns True if deleted, False if not found."""
        items = self._read()
        original_len = len(items)
        items = [item for item in items if item.get("id") != item_id]
        if len(items) < original_len:
            self._write(items)
            return True
        return False

    def count(self) -> int:
        """Return total number of records."""
        return len(self._read())

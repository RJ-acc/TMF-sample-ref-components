from __future__ import annotations

import copy
import logging
import os
import threading
from typing import Any

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - optional at runtime
    MongoClient = None

logger = logging.getLogger(__name__)


def _matches(document: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if value in ("", None):
            continue
        if str(document.get(key)) != str(value):
            return False
    return True


class DocumentStore:
    """Very small document store with MongoDB-first, in-memory fallback behavior."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._memory: dict[str, dict[str, dict[str, Any]]] = {}
        self._backend = "memory"
        self._db = None

        host = os.getenv("MONGODB_HOST", "").strip()
        port = int(os.getenv("MONGODB_PORT", "27017"))
        database = os.getenv("MONGODB_DATABASE", "tmfc023")

        if not host or MongoClient is None:
            logger.info("Document store using in-memory backend")
            return

        try:
            client = MongoClient(host=host, port=port, serverSelectionTimeoutMS=500)
            client.admin.command("ping")
            self._db = client[database]
            self._backend = "mongo"
            logger.info("Document store using MongoDB backend at %s:%s/%s", host, port, database)
        except Exception as exc:  # pragma: no cover - depends on runtime infra
            logger.warning("MongoDB not reachable, falling back to memory: %s", exc)

    @property
    def backend(self) -> str:
        return self._backend

    def list_documents(
        self,
        collection: str,
        filters: dict[str, Any] | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        filters = {k: v for k, v in (filters or {}).items() if v not in ("", None)}

        if self._backend == "mongo":  # pragma: no cover - depends on runtime infra
            cursor = self._db[collection].find(filters, {"_id": 0}).skip(max(offset, 0))
            if limit is not None:
                cursor = cursor.limit(max(limit, 0))
            return [copy.deepcopy(doc) for doc in cursor]

        with self._lock:
            docs = [
                copy.deepcopy(document)
                for document in self._memory.setdefault(collection, {}).values()
                if _matches(document, filters)
            ]
        docs.sort(key=lambda item: (item.get("lastUpdate", ""), item.get("id", "")))
        start = max(offset, 0)
        end = None if limit is None else start + max(limit, 0)
        return docs[start:end]

    def get_document(self, collection: str, document_id: str) -> dict[str, Any] | None:
        if self._backend == "mongo":  # pragma: no cover - depends on runtime infra
            document = self._db[collection].find_one({"id": document_id}, {"_id": 0})
            return copy.deepcopy(document) if document else None

        with self._lock:
            document = self._memory.setdefault(collection, {}).get(document_id)
            return copy.deepcopy(document) if document else None

    def create_document(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        doc = copy.deepcopy(document)
        document_id = doc["id"]

        if self.get_document(collection, document_id):
            raise ValueError(f"Document '{document_id}' already exists in '{collection}'")

        if self._backend == "mongo":  # pragma: no cover - depends on runtime infra
            self._db[collection].insert_one(doc)
            return doc

        with self._lock:
            self._memory.setdefault(collection, {})[document_id] = doc
        return doc

    def replace_document(self, collection: str, document_id: str, document: dict[str, Any]) -> dict[str, Any]:
        doc = copy.deepcopy(document)

        if self._backend == "mongo":  # pragma: no cover - depends on runtime infra
            self._db[collection].replace_one({"id": document_id}, doc, upsert=True)
            return doc

        with self._lock:
            self._memory.setdefault(collection, {})[document_id] = doc
        return doc

    def delete_document(self, collection: str, document_id: str) -> bool:
        if self._backend == "mongo":  # pragma: no cover - depends on runtime infra
            result = self._db[collection].delete_one({"id": document_id})
            return result.deleted_count > 0

        with self._lock:
            return self._memory.setdefault(collection, {}).pop(document_id, None) is not None

    def reset(self) -> None:
        if self._backend == "mongo":  # pragma: no cover - depends on runtime infra
            for collection_name in self._db.list_collection_names():
                self._db[collection_name].delete_many({})
            return

        with self._lock:
            self._memory = {}


STORE = DocumentStore()


def get_store() -> DocumentStore:
    return STORE

"""
KazKaz AI — LLM Response Cache
=================================
Aynı rapor + aynı soru → LLM'e ikinci kez gitme.
Backend pluggable: InMemory (test/dev) veya Firestore (prod).

TTL 24 saat default — finansal veri günde bir güncellenir varsayımı.
Deterministik key: sha256(user_id + prompt + context).

Kullanım:
    from llm_cache import LLMCache, InMemoryCacheBackend
    cache = LLMCache(backend=InMemoryCacheBackend(), ttl_hours=24)

    # gemini_engine.py içine geçir
    ai = GeminiEngine(api_key=..., guardrail=g, cache=cache, user_id="u1")

Firestore ile kalıcı:
    from google.cloud import firestore
    db = firestore.Client()
    cache = LLMCache(backend=FirestoreCacheBackend(db), ttl_hours=24)
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class CacheBackend(ABC):
    """Cache backend arayüzü — swap edilebilir (test/dev vs. prod Firestore)."""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        ...

    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        ...

    @abstractmethod
    def clear(self, user_id: Optional[str] = None) -> int:
        """
        user_id=None → tüm cache sil, sayı döner.
        user_id verilirse → sadece o kullanıcının kayıtları.
        """


class InMemoryCacheBackend(CacheBackend):
    """
    Süreç içi cache. Streamlit oturumu boyunca yaşar.
    Prod'da fayda sınırlı — birden çok worker varsa paylaşılmaz.
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._store[key] = {
            "value": value,
            "expires": time.time() + ttl_seconds,
            "user_id": key.split(":", 2)[1] if ":" in key else "_anon",
        }

    def clear(self, user_id: Optional[str] = None) -> int:
        if user_id is None:
            n = len(self._store)
            self._store.clear()
            return n
        pref = f"user:{user_id}:"
        keys = [k for k in self._store if k.startswith(pref)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def size(self) -> int:
        """Debug/test için."""
        return len(self._store)


class FirestoreCacheBackend(CacheBackend):
    """
    Firestore koleksiyonu (default 'llm_cache'). Her doküman:
      { value: str, expires: float, user_id: str, created: float }

    Prod önerisi: Firestore TTL policy ekle → expires field'a
    otomatik silme. Bu backend expires'i her get'te de kontrol eder
    (defence in depth).

    NOT: firestore_client argümanı, google.cloud.firestore.Client
    ya da uyumlu bir doubles/mock olabilir. Bu modül firestore
    paketini import etmez — çağıran taraf kurar.
    """

    def __init__(self, firestore_client, collection: str = "llm_cache"):
        self._db = firestore_client
        self._col = collection

    def _coll(self):
        return self._db.collection(self._col)

    def get(self, key: str) -> Optional[str]:
        doc = self._coll().document(key).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        if data.get("expires", 0) < time.time():
            try:
                doc.reference.delete()
            except Exception:
                pass
            return None
        return data.get("value")

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        parts = key.split(":", 2)
        user_id = parts[1] if len(parts) >= 2 else "_anon"
        self._coll().document(key).set({
            "value": value,
            "expires": time.time() + ttl_seconds,
            "user_id": user_id,
            "created": time.time(),
        })

    def clear(self, user_id: Optional[str] = None) -> int:
        count = 0
        if user_id is None:
            for doc in self._coll().stream():
                try:
                    doc.reference.delete()
                    count += 1
                except Exception:
                    pass
        else:
            q = self._coll().where("user_id", "==", user_id)
            for doc in q.stream():
                try:
                    doc.reference.delete()
                    count += 1
                except Exception:
                    pass
        return count


class LLMCache:
    """
    LLM cevap cache'i. Backend'e bakmadan tekil bir API.

    _key: kullanıcı, prompt ve context'in birleştirilmiş hash'i.
          Prod'da model adı ve provider da context'e girmeli
          (gemini_engine bunu geçiyor).
    """

    def __init__(
        self,
        backend: Optional[CacheBackend] = None,
        ttl_hours: int = 24,
    ):
        if ttl_hours <= 0:
            raise ValueError("ttl_hours > 0 olmalı.")
        self.backend = backend or InMemoryCacheBackend()
        self.ttl_seconds = ttl_hours * 3600
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _key(
        user_id: Optional[str],
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        uid = user_id or "_anon"
        payload = {"p": prompt, "c": context or {}}
        serialized = json.dumps(
            payload, sort_keys=True, ensure_ascii=False, default=str
        )
        h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"user:{uid}:{h}"

    def get(
        self,
        user_id: Optional[str],
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        key = self._key(user_id, prompt, context)
        val = self.backend.get(key)
        if val is not None:
            self._hits += 1
        else:
            self._misses += 1
        return val

    def set(
        self,
        user_id: Optional[str],
        prompt: str,
        context: Optional[Dict[str, Any]],
        value: str,
    ) -> None:
        if not value:
            return
        key = self._key(user_id, prompt, context)
        self.backend.set(key, value, self.ttl_seconds)

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "hits":         self._hits,
            "misses":       self._misses,
            "total":        total,
            "hit_rate_pct": round(self._hits / total * 100, 1) if total > 0 else 0.0,
        }

    def clear(self, user_id: Optional[str] = None) -> int:
        return self.backend.clear(user_id)

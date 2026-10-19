import asyncio
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class CachedToken:
    token: str
    expires_at: float


class TokenCache:
    def __init__(self):
        self._cache: dict[str, CachedToken] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def get(self, key: str) -> Optional[str]:
        entry = self._cache.get(key)
        if entry and entry.expires_at > time.time():
            return entry.token
        return None

    def set(self, key: str, token: str, ttl: int):
        self._cache[key] = CachedToken(token=token, expires_at=time.time() + ttl)

    def lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]


token_cache = TokenCache()

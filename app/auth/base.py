from abc import ABC, abstractmethod

import httpx


class AuthStrategy(ABC):
    @abstractmethod
    async def apply(self, headers: dict, client: httpx.AsyncClient) -> dict:
        """Mutate/return headers with auth info injected."""
        ...

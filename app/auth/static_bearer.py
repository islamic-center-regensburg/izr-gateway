import httpx

from app.auth.base import AuthStrategy
from app.config import StaticBearerConfig


class StaticBearerAuth(AuthStrategy):
    def __init__(self, name: str, config: StaticBearerConfig):
        self.name = name
        self.config = config

    async def apply(self, headers: dict, client: httpx.AsyncClient) -> dict:
        headers["Authorization"] = f"Bearer {self.config.token}"
        return headers

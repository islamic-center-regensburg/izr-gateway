import httpx

from app.auth.base import AuthStrategy
from app.config import ApiKeyConfig


class ApiKeyAuth(AuthStrategy):
    def __init__(self, name: str, config: ApiKeyConfig):
        self.name = name
        self.config = config

    async def apply(self, headers: dict, client: httpx.AsyncClient) -> dict:
        headers[self.config.header] = self.config.value
        return headers

import httpx

from app.auth.base import AuthStrategy
from app.config import OIDCClientCredentialsConfig
from app.token_cache import token_cache


class OIDCClientCredentialsAuth(AuthStrategy):
    def __init__(self, name: str, config: OIDCClientCredentialsConfig):
        self.name = name
        self.config = config
        self.cache_key = f"oidc:{name}"

    async def _fetch_token(self, client: httpx.AsyncClient) -> str:
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }
        if self.config.scope:
            data["scope"] = self.config.scope

        resp = await client.post(
            self.config.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        payload = resp.json()
        token = payload["access_token"]
        ttl = min(payload.get("expires_in", 3600) - 60, self.config.cache_ttl)
        token_cache.set(self.cache_key, token, ttl)
        return token

    async def apply(self, headers: dict, client: httpx.AsyncClient) -> dict:
        token = token_cache.get(self.cache_key)
        if not token:
            async with token_cache.lock(self.cache_key):
                token = token_cache.get(self.cache_key)
                if not token:
                    token = await self._fetch_token(client)
        headers["Authorization"] = f"Bearer {token}"
        return headers

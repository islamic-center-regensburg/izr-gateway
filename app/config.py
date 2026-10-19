import os
import re
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field

ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _expand_env(value):
    """Recursively expand ${VAR} in strings."""
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


# -------- Auth Provider Schemas --------
class OIDCClientCredentialsConfig(BaseModel):
    type: Literal["oidc_client_credentials"]
    token_url: str
    client_id: str
    client_secret: str
    scope: Optional[str] = None
    cache_ttl: int = 3300


class ApiKeyConfig(BaseModel):
    type: Literal["api_key"]
    header: str = "X-API-Key"
    value: str


class StaticBearerConfig(BaseModel):
    type: Literal["static_bearer"]
    token: str


AuthProviderConfig = OIDCClientCredentialsConfig | ApiKeyConfig | StaticBearerConfig


# -------- Route Schema --------
class RouteConfig(BaseModel):
    name: str
    path_prefix: str
    upstream: str
    strip_prefix: bool = True
    rewrite_prefix: Optional[str] = None
    auth: Optional[str] = None
    timeout: int = 30


# -------- Server Schema --------
class CORSConfig(BaseModel):
    allow_origins: list[str] = ["*"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    cors: CORSConfig = Field(default_factory=CORSConfig)


class GatewayConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    auth_providers: dict[str, AuthProviderConfig] = Field(default_factory=dict)
    routes: list[RouteConfig] = Field(default_factory=list)


def load_config(path: str = "config.yaml") -> GatewayConfig:
    raw = yaml.safe_load(Path(path).read_text())
    expanded = _expand_env(raw)
    return GatewayConfig(**expanded)

from app.auth.api_key import ApiKeyAuth
from app.auth.base import AuthStrategy
from app.auth.oidc_client_credentials import OIDCClientCredentialsAuth
from app.auth.static_bearer import StaticBearerAuth
from app.config import (
    ApiKeyConfig,
    OIDCClientCredentialsConfig,
    StaticBearerConfig,
)


def build_auth_strategy(name: str, config) -> AuthStrategy:
    if isinstance(config, OIDCClientCredentialsConfig):
        return OIDCClientCredentialsAuth(name, config)
    if isinstance(config, ApiKeyConfig):
        return ApiKeyAuth(name, config)
    if isinstance(config, StaticBearerConfig):
        return StaticBearerAuth(name, config)
    raise ValueError(f"Unknown auth type for provider '{name}'")

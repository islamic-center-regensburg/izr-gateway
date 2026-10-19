import os
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.auth import build_auth_strategy
from app.config import load_config
from app.proxy import proxy_request

load_dotenv()

CONFIG_PATH = os.getenv("GATEWAY_CONFIG", "config.yaml")
config = load_config(CONFIG_PATH)

auth_strategies = {
    name: build_auth_strategy(name, cfg) for name, cfg in config.auth_providers.items()
}

sorted_routes = sorted(config.routes, key=lambda r: len(r.path_prefix), reverse=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient()
    yield
    await app.state.http.aclose()


app = FastAPI(title="FastAPI Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors.allow_origins,
    allow_methods=config.server.cors.allow_methods,
    allow_headers=config.server.cors.allow_headers,
    allow_credentials=True,
)


@app.get("/_gateway/health")
async def health():
    return {"status": "ok", "routes": [r.name for r in config.routes]}


@app.get("/_gateway/routes")
async def list_routes():
    return [
        {
            "name": r.name,
            "path_prefix": r.path_prefix,
            "upstream": r.upstream,
            "auth": r.auth,
        }
        for r in config.routes
    ]


def match_route(path: str):
    for route in sorted_routes:
        if path.startswith(route.path_prefix):
            return route
    return None


@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def gateway(full_path: str, request: Request):
    path = "/" + full_path
    route = match_route(path)
    if not route:
        raise HTTPException(status_code=404, detail="No route matched")

    auth = auth_strategies.get(route.auth) if route.auth else None
    if route.auth and not auth:
        raise HTTPException(
            status_code=500,
            detail=f"Auth provider '{route.auth}' not configured",
        )

    return await proxy_request(request, route, auth, request.app.state.http)

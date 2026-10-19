import httpx
from fastapi import Request, Response

from app.auth.base import AuthStrategy
from app.config import RouteConfig

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def build_upstream_url(route: RouteConfig, request_path: str) -> str:
    path = request_path
    if route.strip_prefix and path.startswith(route.path_prefix):
        path = path[len(route.path_prefix) :]
    if route.rewrite_prefix:
        path = route.rewrite_prefix.rstrip("/") + "/" + path.lstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return route.upstream.rstrip("/") + path


async def proxy_request(
    request: Request,
    route: RouteConfig,
    auth: AuthStrategy | None,
    client: httpx.AsyncClient,
) -> Response:
    url = build_upstream_url(route, request.url.path)

    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP}

    if auth:
        headers = await auth.apply(headers, client)

    body = await request.body()

    try:
        upstream_resp = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=body,
            timeout=route.timeout,
            follow_redirects=False,
        )
    except httpx.TimeoutException:
        return Response(content="Upstream timeout", status_code=504)
    except httpx.RequestError as e:
        return Response(content=f"Upstream error: {e}", status_code=502)

    resp_headers = {
        k: v for k, v in upstream_resp.headers.items() if k.lower() not in HOP_BY_HOP
    }

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
    )

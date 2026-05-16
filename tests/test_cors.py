"""CORS ミドルウェアの設定確認."""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_options_health_returns_valid_cors():
    """OPTIONS /health が CORS ヘッダーを返す."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.options(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
    assert resp.status_code == 200
    # CORS ミドルウェアが有効であれば Access-Control-Allow-Origin が付く
    assert "access-control-allow-origin" in resp.headers


@pytest.mark.asyncio
async def test_health_includes_cors_header():
    """GET /health で CORS ヘッダーが返る."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
    assert "access-control-allow-origin" in resp.headers

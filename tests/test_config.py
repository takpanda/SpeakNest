"""GET /api/config のテスト."""
import os
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.routers.config import ConfigResponse, EXPECTED_VARS


@pytest.mark.asyncio
async def test_config_returns_200():
    """GET /api/config のレスポンスが HTTP 200 を返す."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_config_response_schema():
    """GET /api/config のレスポンスが ConfigResponse スキーマに適合する."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config")
    data = resp.json()
    validated = ConfigResponse.model_validate(data)
    assert isinstance(validated.configured, list)
    assert isinstance(validated.missing, list)


@pytest.mark.asyncio
async def test_config_expected_vars_count():
    """EXPECTED_VARS の数は 7 件."""
    assert len(EXPECTED_VARS) == 7


@pytest.mark.asyncio
async def test_config_all_missing_when_no_env():
    """全環境変数が未設定の場合、missing に全 7 件が含まれる."""
    # 既存の環境変数を退避
    originals = {k: os.environ.get(k) for k in EXPECTED_VARS}
    try:
        # 全 vars を削除
        for k in EXPECTED_VARS:
            os.environ.pop(k, None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/config")
        data = resp.json()
        for env_name in EXPECTED_VARS:
            assert env_name in data["missing"], f"{env_name} が missing に含まれていない"
        assert len(data["configured"]) == 0
    finally:
        # 元の値を復元
        for k, v in originals.items():
            if v is not None:
                os.environ[k] = v


@pytest.mark.asyncio
async def test_config_all_configured_when_all_set():
    """全環境変数が設定されている場合、configured に全 7 件が含まれる."""
    originals = {k: os.environ.get(k) for k in EXPECTED_VARS}
    try:
        # 全 vars を設定
        os.environ["OLLAMA_BASE_URL"] = "http://ollama:11434"
        os.environ["WHISPER_BASE_URL"] = "http://whisper:8000"
        os.environ["TTS_BASE_URL"] = "http://tts:5000"
        os.environ["DATA_DIR"] = "/data"
        os.environ["RECORDINGS_DIR"] = "/recordings"
        os.environ["DATABASE_URL"] = "sqlite:///./data.db"
        os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/config")
        data = resp.json()
        for env_name in EXPECTED_VARS:
            assert env_name in data["configured"], f"{env_name} が configured に含まれていない"
        assert len(data["missing"]) == 0
    finally:
        for k, v in originals.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)


@pytest.mark.asyncio
async def test_config_partial_configuration():
    """一部だけ設定されている場合、configured / missing が正しい."""
    originals = {k: os.environ.get(k) for k in EXPECTED_VARS}
    try:
        # OLLAMA_BASE_URL のみ設定
        os.environ["OLLAMA_BASE_URL"] = "http://ollama:11434"
        for k in EXPECTED_VARS[1:]:
            os.environ.pop(k, None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/config")
        data = resp.json()
        assert "OLLAMA_BASE_URL" in data["configured"]
        for env_name in EXPECTED_VARS[1:]:
            assert env_name in data["missing"], f"{env_name} が missing に含まれていない"
    finally:
        for k, v in originals.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

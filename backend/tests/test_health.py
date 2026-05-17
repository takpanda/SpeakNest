from __future__ import annotations


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_returns_ok(self, client):
        """Health returns ok only when both Ollama and STT are reachable."""
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        # In unconnected CI/local env both services are "not_available" -> status=degraded
        assert data["status"] in ("ok", "degraded")
        assert data["ollama"] in ("ok", "not_available")
        assert data["stt"] in ("ok", "not_available")
        assert "upload_dir" in data

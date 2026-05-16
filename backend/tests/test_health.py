from __future__ import annotations


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_returns_ok(self, client, _mock_ollama):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["ollama"] == "ok"
        assert data["stt"] == "ok"
        assert "upload_dir" in data

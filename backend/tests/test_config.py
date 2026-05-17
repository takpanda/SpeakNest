from __future__ import annotations


class TestConfigEndpoint:
    def test_config_endpoint_available(self, client):
        res = client.get("/api/config")
        assert res.status_code == 200
        body = res.json()
        assert "configured" in body
        assert "missing" in body

    def test_config_uses_speaknest_prefixed_env_names(self, client, monkeypatch):
        monkeypatch.setenv("SPEAKNEST_OLLAMA_BASE_URL", "http://localhost:11434")
        res = client.get("/api/config")
        assert res.status_code == 200
        body = res.json()
        assert "SPEAKNEST_OLLAMA_BASE_URL" in body["configured"]

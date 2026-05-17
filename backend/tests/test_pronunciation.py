from __future__ import annotations


class TestPronunciationEndpoint:
    def test_pronunciation_endpoint_available(self, client):
        res = client.post(
            "/pronunciation",
            json={
                "target_sentence": "Hello world.",
                "transcript": "Hello world",
                "sentence_mode": False,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "wer" in data
        assert "llm_context" in data

    def test_pronunciation_empty_inputs(self, client):
        res = client.post(
            "/pronunciation",
            json={"target_sentence": "", "transcript": "", "sentence_mode": False},
        )
        assert res.status_code == 400

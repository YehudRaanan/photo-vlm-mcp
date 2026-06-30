import pytest

from photo_vlm_mcp.config import Config
from photo_vlm_mcp.ollama import OllamaClient


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"model": "qwen3-vl:8b", "message": {"content": "ok"}}


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.payload = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, json):
        self.payload = json
        return FakeResponse()


@pytest.mark.asyncio
async def test_ollama_chat_posts_api_chat(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", FakeAsyncClient)

    result = await OllamaClient(Config()).chat(
        model="qwen3-vl:8b",
        prompt="describe",
        images_b64=["abc"],
    )

    assert result.text == "ok"
    assert result.model == "qwen3-vl:8b"

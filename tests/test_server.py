from __future__ import annotations

import base64
from io import BytesIO

import pytest
from PIL import Image

from photo_vlm_mcp.config import Config
from photo_vlm_mcp.ollama import OllamaResult
from photo_vlm_mcp.server import create_server


def encoded_photo(color: str = "white") -> str:
    output = BytesIO()
    Image.new("RGB", (40, 30), color=color).save(output, format="JPEG")
    return base64.b64encode(output.getvalue()).decode("ascii")


class FakeOllama:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def chat(
        self,
        *,
        model: str,
        prompt: str,
        images_b64: list[str],
        max_tokens: int | None = None,
        temperature: float = 0.2,
    ) -> OllamaResult:
        self.calls.append(
            {
                "model": model,
                "prompt": prompt,
                "images": len(images_b64),
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )
        return OllamaResult(text='{"summary":"ok","differences":[]}', model=model, latency_ms=12)

    async def list_models(self) -> list[str]:
        return ["photo-model", "ocr-model"]


async def call_structured(server, name: str, arguments: dict) -> dict:
    _content, structured = await server.call_tool(name, arguments)
    return structured


@pytest.mark.asyncio
async def test_mcp_lists_expected_tools():
    server = create_server(Config(photo_model="photo-model", ocr_model="ocr-model"), FakeOllama())

    tools = await server.list_tools()

    assert {tool.name for tool in tools} == {
        "analyze_photo",
        "photo_ocr",
        "inspect_scene",
        "compare_photos",
        "extract_metadata",
        "health",
    }


@pytest.mark.asyncio
async def test_mcp_analyze_photo_calls_ollama():
    ollama = FakeOllama()
    server = create_server(Config(photo_model="photo-model", ocr_model="ocr-model"), ollama)

    result = await call_structured(
        server,
        "analyze_photo",
        {"image_b64": encoded_photo(), "prompt": "What is visible?", "max_tokens": 64},
    )

    assert result["model"] == "photo-model"
    assert result["latency_ms"] == 12
    assert ollama.calls[0]["images"] == 1
    assert ollama.calls[0]["max_tokens"] == 64


@pytest.mark.asyncio
async def test_mcp_extract_metadata_does_not_call_ollama():
    ollama = FakeOllama()
    server = create_server(Config(photo_model="photo-model", ocr_model="ocr-model"), ollama)

    result = await call_structured(
        server,
        "extract_metadata",
        {"image_b64": encoded_photo(), "include_exif": False, "include_hash": True},
    )

    assert result["width"] == 40
    assert result["height"] == 30
    assert result["sha256"]
    assert ollama.calls == []


@pytest.mark.asyncio
async def test_mcp_compare_photos_sends_two_images():
    ollama = FakeOllama()
    server = create_server(Config(photo_model="photo-model", ocr_model="ocr-model"), ollama)

    result = await call_structured(
        server,
        "compare_photos",
        {
            "before": {"image_b64": encoded_photo("white")},
            "after": {"image_b64": encoded_photo("black")},
        },
    )

    assert result["summary"] == "ok"
    assert ollama.calls[0]["images"] == 2


@pytest.mark.asyncio
async def test_mcp_health_reports_missing_models():
    server = create_server(Config(photo_model="photo-model", ocr_model="missing-ocr"), FakeOllama())

    result = await call_structured(server, "health", {})

    assert result["ollama_reachable"] is True
    assert result["missing_models"] == ["missing-ocr"]

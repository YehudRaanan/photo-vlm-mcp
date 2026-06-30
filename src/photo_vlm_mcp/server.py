from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from photo_vlm_mcp import __version__
from photo_vlm_mcp.config import Config
from photo_vlm_mcp.errors import PhotoVlmError
from photo_vlm_mcp.images import metadata_for, resolve_photo
from photo_vlm_mcp.ocr import run_photo_ocr
from photo_vlm_mcp.ollama import OllamaClient
from photo_vlm_mcp.prompts import (
    analyze_photo_prompt,
    compare_photos_prompt,
    inspect_scene_prompt,
)

SERVER_VERSION = __version__


def create_server(config: Config | None = None, ollama: OllamaClient | None = None) -> FastMCP:
    cfg = config or Config.from_env()
    client = ollama or OllamaClient(cfg)
    mcp = FastMCP("photo-vlm-mcp")

    @mcp.tool()
    async def analyze_photo(
        path: str | None = None,
        url: str | None = None,
        image_b64: str | None = None,
        prompt: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        detail: str = "normal",
    ) -> dict[str, Any]:
        """Analyze or answer a question about a real-world camera photo."""
        photo = resolve_photo(cfg, path=path, url=url, image_b64=image_b64)
        result = await client.chat(
            model=model or cfg.photo_model,
            prompt=analyze_photo_prompt(prompt=prompt, detail=detail),
            images_b64=[photo.base64],
            max_tokens=max_tokens,
        )
        return {"text": result.text, "model": result.model, "latency_ms": result.latency_ms}

    @mcp.tool()
    async def photo_ocr(
        path: str | None = None,
        url: str | None = None,
        image_b64: str | None = None,
        engine: str = "vlm",
        model: str | None = None,
        structured: bool = False,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Extract text from a camera photo: labels, receipts, signs, whiteboards, or pages."""
        photo = resolve_photo(cfg, path=path, url=url, image_b64=image_b64)
        return await run_photo_ocr(
            cfg,
            client,
            photo,
            engine=engine,
            model=model,
            structured=structured,
            language=language,
        )

    @mcp.tool()
    async def inspect_scene(
        path: str | None = None,
        url: str | None = None,
        image_b64: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        include_uncertainty: bool = True,
    ) -> dict[str, Any]:
        """Return structured scene context, objects, text, quality, and uncertainty."""
        photo = resolve_photo(cfg, path=path, url=url, image_b64=image_b64)
        result = await client.chat(
            model=model or cfg.photo_model,
            prompt=inspect_scene_prompt(focus=focus, include_uncertainty=include_uncertainty),
            images_b64=[photo.base64],
        )
        return _json_or_text(result.text) | {"model": result.model, "latency_ms": result.latency_ms}

    @mcp.tool()
    async def compare_photos(
        before: dict[str, str | None],
        after: dict[str, str | None],
        question: str | None = None,
        model: str | None = None,
        detail: str = "normal",
    ) -> dict[str, Any]:
        """Compare two real-world photos for visible differences or subject similarity."""
        first = resolve_photo(
            cfg,
            path=before.get("path"),
            url=before.get("url"),
            image_b64=before.get("image_b64"),
        )
        second = resolve_photo(
            cfg,
            path=after.get("path"),
            url=after.get("url"),
            image_b64=after.get("image_b64"),
        )
        result = await client.chat(
            model=model or cfg.photo_model,
            prompt=compare_photos_prompt(question=question, detail=detail),
            images_b64=[first.base64, second.base64],
        )
        return _json_or_text(result.text) | {"model": result.model, "latency_ms": result.latency_ms}

    @mcp.tool()
    async def extract_metadata(
        path: str | None = None,
        url: str | None = None,
        image_b64: str | None = None,
        include_exif: bool = True,
        include_hash: bool = False,
    ) -> dict[str, Any]:
        """Extract technical photo metadata without calling the VLM."""
        photo = resolve_photo(cfg, path=path, url=url, image_b64=image_b64)
        return metadata_for(photo, include_exif=include_exif, include_hash=include_hash)

    @mcp.tool()
    async def health() -> dict[str, Any]:
        """Check Ollama reachability and configured model availability."""
        try:
            available = await client.list_models()
            reachable = True
        except PhotoVlmError:
            available = []
            reachable = False
        configured = {"photo": cfg.photo_model, "ocr": cfg.ocr_model}
        return {
            "ollama_reachable": reachable,
            "ollama_url": cfg.ollama_url,
            "available_models": available,
            "configured": configured,
            "missing_models": [m for m in configured.values() if m not in available],
            "server_version": SERVER_VERSION,
        }

    return mcp


def _json_or_text(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"summary": text}
    return parsed if isinstance(parsed, dict) else {"summary": text}


def run_server() -> None:
    create_server().run()


__all__ = ["SERVER_VERSION", "create_server", "run_server"]

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import httpx

from photo_vlm_mcp.config import Config
from photo_vlm_mcp.errors import PhotoVlmError


@dataclass(frozen=True)
class OllamaResult:
    text: str
    model: str
    latency_ms: int


class OllamaClient:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def chat(
        self,
        *,
        model: str,
        prompt: str,
        images_b64: list[str],
        max_tokens: int | None = None,
        temperature: float = 0.2,
    ) -> OllamaResult:
        started = time.perf_counter()
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt, "images": images_b64}],
            "stream": False,
            "keep_alive": self.config.keep_alive,
            "options": {
                "num_predict": max_tokens or self.config.max_tokens,
                "temperature": temperature,
            },
        }
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.post(
                        f"{self.config.ollama_url.rstrip('/')}/api/chat",
                        json=payload,
                    )
                if response.status_code == 404:
                    raise PhotoVlmError(f"Model '{model}' not found. Run `ollama pull {model}`.")
                response.raise_for_status()
                body = response.json()
                text = body.get("message", {}).get("content", "")
                return OllamaResult(
                    text=text,
                    model=body.get("model", model),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
                last_error = exc
                if attempt == 0:
                    await asyncio.sleep(0.2)
                    continue
                raise PhotoVlmError(
                    f"Cannot reach Ollama at {self.config.ollama_url}. "
                    "Start it with `ollama serve`."
                ) from exc
            except httpx.TimeoutException as exc:
                raise PhotoVlmError(
                    f"VLM request exceeded {self.config.timeout}s; "
                    "try a smaller image or lighter model."
                ) from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt == 0:
                    last_error = exc
                    await asyncio.sleep(0.2)
                    continue
                raise PhotoVlmError(
                    f"Ollama request failed: HTTP {exc.response.status_code}"
                ) from exc
        raise PhotoVlmError(f"Ollama request failed: {last_error}")

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config.ollama_url.rstrip('/')}/api/tags")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PhotoVlmError(
                f"Cannot reach Ollama at {self.config.ollama_url}. Start it with `ollama serve`."
            ) from exc
        body: dict[str, Any] = response.json()
        return [item["name"] for item in body.get("models", []) if "name" in item]

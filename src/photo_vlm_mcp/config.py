from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _getenv(primary: str, default: str, *aliases: str) -> str:
    for name in (primary, *aliases):
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return default


def _getint(primary: str, default: int, *aliases: str) -> int:
    raw = _getenv(primary, str(default), *aliases)
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{primary} must be an integer, got {raw!r}") from exc


def _getfloat(primary: str, default: float, *aliases: str) -> float:
    raw = _getenv(primary, str(default), *aliases)
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{primary} must be a number, got {raw!r}") from exc


def _getbool(primary: str, default: bool, *aliases: str) -> bool:
    raw = _getenv(primary, "1" if default else "0", *aliases).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _split_roots(raw: str) -> tuple[Path, ...]:
    if not raw:
        return ()
    sep = ";" if os.name == "nt" else ":"
    return tuple(Path(part).expanduser().resolve() for part in raw.split(sep) if part.strip())


@dataclass(frozen=True)
class Config:
    ollama_url: str = "http://127.0.0.1:11434"
    photo_model: str = "qwen3-vl:8b"
    ocr_model: str = "minicpm-v"
    max_tokens: int = 1024
    timeout: float = 120.0
    keep_alive: str = "10m"
    max_dim: int = 2048
    max_image_mb: int = 20
    fetch_timeout: float = 15.0
    allow_private_urls: bool = False
    allowed_roots: tuple[Path, ...] = ()
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            ollama_url=_getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
            photo_model=_getenv("PHOTO_VLM_MODEL", "qwen3-vl:8b", "VLM_MODEL"),
            ocr_model=_getenv("PHOTO_OCR_MODEL", "minicpm-v", "OCR_MODEL"),
            max_tokens=_getint("PHOTO_VLM_MAX_TOKENS", 1024, "VLM_MAX_TOKENS"),
            timeout=_getfloat("PHOTO_VLM_TIMEOUT", 120.0, "VLM_TIMEOUT"),
            keep_alive=_getenv("PHOTO_VLM_KEEP_ALIVE", "10m", "VLM_KEEP_ALIVE"),
            max_dim=_getint("PHOTO_VLM_MAX_DIM", 2048, "VLM_MAX_DIM"),
            max_image_mb=_getint("PHOTO_VLM_MAX_IMAGE_MB", 20, "VLM_MAX_IMAGE_MB"),
            fetch_timeout=_getfloat("PHOTO_VLM_FETCH_TIMEOUT", 15.0, "VLM_FETCH_TIMEOUT"),
            allow_private_urls=_getbool(
                "PHOTO_VLM_ALLOW_PRIVATE_URLS", False, "VLM_ALLOW_PRIVATE_URLS"
            ),
            allowed_roots=_split_roots(_getenv("PHOTO_VLM_ALLOWED_ROOTS", "", "VLM_ALLOWED_ROOTS")),
            log_level=_getenv("PHOTO_VLM_LOG_LEVEL", "INFO", "VLM_LOG_LEVEL"),
        )

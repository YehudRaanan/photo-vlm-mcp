from __future__ import annotations

import base64
import hashlib
import ipaddress
import socket
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

from photo_vlm_mcp.config import Config
from photo_vlm_mcp.errors import PhotoVlmError

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF", "BMP", "HEIC", "HEIF"}


@dataclass(frozen=True)
class PhotoInput:
    data: bytes
    original_data: bytes
    format: str
    width: int
    height: int
    source: str
    original_path: Path | None = None

    @property
    def base64(self) -> str:
        return base64.b64encode(self.data).decode("ascii")


def ensure_one_source(path: str | None, url: str | None, image_b64: str | None) -> None:
    count = sum(bool(x) for x in (path, url, image_b64))
    if count != 1:
        raise PhotoVlmError("Provide exactly one of: path, url, image_b64.")


def resolve_photo(
    config: Config,
    *,
    path: str | None = None,
    url: str | None = None,
    image_b64: str | None = None,
) -> PhotoInput:
    ensure_one_source(path, url, image_b64)
    if path:
        data, source, original_path = _read_path(config, path)
    elif url:
        data, source, original_path = _read_url(config, url), url, None
    else:
        data, source, original_path = _decode_b64(image_b64 or ""), "base64", None
    return _validate_and_normalize(config, data, source, original_path)


def metadata_for(photo: PhotoInput, include_exif: bool, include_hash: bool) -> dict[str, Any]:
    with Image.open(BytesIO(photo.original_data)) as img:
        exif_raw = img.getexif() if include_exif else {}
        exif = _extract_exif(exif_raw) if include_exif else {}
    return {
        "format": photo.format,
        "width": photo.width,
        "height": photo.height,
        "orientation": exif.get("orientation"),
        "exif": (
            {
                "datetime_original": exif.get("datetime_original"),
                "gps": exif.get("gps"),
                "camera_make": exif.get("camera_make"),
                "camera_model": exif.get("camera_model"),
                "focal_length": exif.get("focal_length"),
            }
            if include_exif
            else {}
        ),
        "sha256": hashlib.sha256(photo.original_data).hexdigest() if include_hash else None,
    }


def _read_path(config: Config, raw_path: str) -> tuple[bytes, str, Path]:
    photo_path = Path(raw_path).expanduser()
    if not photo_path.is_absolute():
        raise PhotoVlmError("Path input must be absolute.")
    resolved = photo_path.resolve()
    if config.allowed_roots and not any(
        _is_relative_to(resolved, root) for root in config.allowed_roots
    ):
        raise PhotoVlmError(f"Path {resolved} is outside PHOTO_VLM_ALLOWED_ROOTS.")
    if not resolved.is_file():
        raise PhotoVlmError(f"Photo path does not exist or is not a file: {resolved}")
    data = resolved.read_bytes()
    return data, str(resolved), resolved


def _read_url(config: Config, raw_url: str) -> bytes:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise PhotoVlmError("URL input must be http(s).")
    if not config.allow_private_urls and _is_private_host(parsed.hostname):
        raise PhotoVlmError("Private, loopback, and link-local URLs are blocked by default.")
    with httpx.Client(timeout=config.fetch_timeout, follow_redirects=True) as client:
        response = client.get(raw_url)
        response.raise_for_status()
    return response.content


def _decode_b64(raw: str) -> bytes:
    payload = raw.split(",", 1)[1] if raw.startswith("data:") and "," in raw else raw
    try:
        return base64.b64decode(payload, validate=True)
    except ValueError as exc:
        raise PhotoVlmError("image_b64 is not valid base64.") from exc


def _validate_and_normalize(
    config: Config, data: bytes, source: str, original_path: Path | None
) -> PhotoInput:
    max_bytes = config.max_image_mb * 1024 * 1024
    if len(data) > max_bytes:
        size_mb = len(data) / 1024 / 1024
        raise PhotoVlmError(
            f"Image {size_mb:.1f}MB exceeds PHOTO_VLM_MAX_IMAGE_MB={config.max_image_mb}."
        )
    try:
        with Image.open(BytesIO(data)) as raw_img:
            raw_format = (raw_img.format or "UNKNOWN").upper()
            if raw_format not in SUPPORTED_FORMATS:
                raise PhotoVlmError(
                    f"Unsupported image type {raw_format}. Supported: PNG/JPEG/WebP/GIF/BMP/HEIC."
                )
            image = ImageOps.exif_transpose(raw_img)
            image.thumbnail((config.max_dim, config.max_dim))
            output = BytesIO()
            save_format = "JPEG" if raw_format in {"HEIC", "HEIF"} else raw_format
            if save_format == "JPEG" and image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            image.save(output, format=save_format)
            normalized = output.getvalue()
            width, height = image.size
            return PhotoInput(
                data=normalized,
                original_data=data,
                format=save_format,
                width=width,
                height=height,
                source=source,
                original_path=original_path,
            )
    except UnidentifiedImageError as exc:
        raise PhotoVlmError("Unsupported or unreadable image data.") from exc


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_private_host(hostname: str) -> bool:
    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise PhotoVlmError(f"Cannot resolve URL hostname: {hostname}") from exc
    for item in addresses:
        ip = ipaddress.ip_address(item[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return True
    return False


def _extract_exif(exif: Any) -> dict[str, Any]:
    gps = _gps_from_exif(exif.get(34853)) if exif else None
    return {
        "orientation": str(exif.get(274)) if exif and exif.get(274) else None,
        "datetime_original": exif.get(36867) if exif else None,
        "gps": gps,
        "camera_make": exif.get(271) if exif else None,
        "camera_model": exif.get(272) if exif else None,
        "focal_length": str(exif.get(37386)) if exif and exif.get(37386) else None,
    }


def _gps_from_exif(gps_info: Any) -> dict[str, float] | None:
    if not gps_info:
        return None
    try:
        lat = _coord_to_float(gps_info[2])
        lon = _coord_to_float(gps_info[4])
        if gps_info.get(1) == "S":
            lat = -lat
        if gps_info.get(3) == "W":
            lon = -lon
        return {"lat": lat, "lon": lon}
    except Exception:
        return None


def _coord_to_float(coord: Any) -> float:
    degrees, minutes, seconds = coord
    return float(degrees) + float(minutes) / 60 + float(seconds) / 3600

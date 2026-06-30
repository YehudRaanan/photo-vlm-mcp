from __future__ import annotations

import base64
import hashlib
from io import BytesIO

import pytest
from PIL import Image

from photo_vlm_mcp.config import Config
from photo_vlm_mcp.errors import PhotoVlmError
from photo_vlm_mcp.images import metadata_for, resolve_photo


def png_bytes(size=(32, 24), color="white") -> bytes:
    output = BytesIO()
    Image.new("RGB", size, color=color).save(output, format="PNG")
    return output.getvalue()


def test_resolve_photo_from_absolute_path(tmp_path):
    photo_path = tmp_path / "photo.png"
    photo_path.write_bytes(png_bytes())

    photo = resolve_photo(Config(), path=str(photo_path.resolve()))

    assert photo.format == "PNG"
    assert photo.width == 32
    assert photo.height == 24


def test_resolve_photo_rejects_multiple_sources(tmp_path):
    photo_path = tmp_path / "photo.png"
    photo_path.write_bytes(png_bytes())

    with pytest.raises(PhotoVlmError, match="exactly one"):
        resolve_photo(Config(), path=str(photo_path.resolve()), image_b64="abc")


def test_resolve_photo_from_base64_data_uri():
    payload = base64.b64encode(png_bytes()).decode("ascii")

    photo = resolve_photo(Config(), image_b64=f"data:image/png;base64,{payload}")

    assert photo.format == "PNG"


def test_metadata_can_include_hash():
    original = png_bytes()
    payload = base64.b64encode(original).decode("ascii")
    photo = resolve_photo(Config(), image_b64=payload)

    metadata = metadata_for(photo, include_exif=True, include_hash=True)

    assert metadata["width"] == 32
    assert metadata["height"] == 24
    assert isinstance(metadata["sha256"], str)
    assert len(metadata["sha256"]) == 64
    assert metadata["sha256"] == hashlib.sha256(original).hexdigest()

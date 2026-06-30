from __future__ import annotations

import argparse
import asyncio
import base64
import sys
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from photo_vlm_mcp.config import Config  # noqa: E402
from photo_vlm_mcp.images import metadata_for, resolve_photo  # noqa: E402
from photo_vlm_mcp.ollama import OllamaClient  # noqa: E402
from photo_vlm_mcp.prompts import analyze_photo_prompt, photo_ocr_prompt  # noqa: E402


def make_fixture() -> bytes:
    image = Image.new("RGB", (900, 600), color=(238, 235, 226))
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 90, 820, 500), outline=(40, 40, 40), width=6)
    draw.text((130, 160), "PHOTO VLM EVAL", fill=(0, 0, 0))
    draw.text((130, 240), "LABEL: ALPHA-42", fill=(0, 0, 0))
    draw.text((130, 320), "DATE: 2026-06-30", fill=(0, 0, 0))
    output = BytesIO()
    image.save(output, format="JPEG", quality=92)
    return output.getvalue()


async def run_live_eval(config: Config, *, strict_ocr: bool) -> int:
    client = OllamaClient(config)
    models = await client.list_models()
    missing = [m for m in {config.photo_model, config.ocr_model} if m not in models]
    if missing:
        print(f"Missing models: {', '.join(missing)}")
        print("Pull them with `ollama pull <model>` or override PHOTO_VLM_MODEL/PHOTO_OCR_MODEL.")
        return 2

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
        handle.write(make_fixture())
        fixture_path = Path(handle.name)

    try:
        photo = resolve_photo(config, path=str(fixture_path))
        metadata = metadata_for(photo, include_exif=False, include_hash=True)
        if metadata["width"] <= 0 or metadata["height"] <= 0 or not metadata["sha256"]:
            print("metadata: FAIL")
            return 3
        print("metadata: PASS")

        analysis = await client.chat(
            model=config.photo_model,
            prompt=analyze_photo_prompt("What text and objects are visible?", "brief"),
            images_b64=[photo.base64],
            max_tokens=256,
        )
        if not analysis.text.strip():
            print("analyze_photo: FAIL empty response")
            return 4
        print("analyze_photo: PASS")

        ocr = await client.chat(
            model=config.ocr_model,
            prompt=photo_ocr_prompt(structured=False, language="eng"),
            images_b64=[base64.b64encode(photo.data).decode("ascii")],
            max_tokens=256,
            temperature=0.0,
        )
        if "ALPHA" not in ocr.text.upper():
            print("photo_ocr: WARN expected ALPHA-42, got:")
            print(ocr.text)
            return 5 if strict_ocr else 0
        print("photo_ocr: PASS")
        return 0
    finally:
        fixture_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run live photo-vlm-mcp Ollama evaluation.")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--photo-model", default=None)
    parser.add_argument("--ocr-model", default=None)
    parser.add_argument("--strict-ocr", action="store_true")
    args = parser.parse_args()

    config = Config.from_env()
    if args.ollama_url or args.photo_model or args.ocr_model:
        config = Config(
            ollama_url=args.ollama_url or config.ollama_url,
            photo_model=args.photo_model or config.photo_model,
            ocr_model=args.ocr_model or config.ocr_model,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            keep_alive=config.keep_alive,
            max_dim=config.max_dim,
            max_image_mb=config.max_image_mb,
            fetch_timeout=config.fetch_timeout,
            allow_private_urls=config.allow_private_urls,
            allowed_roots=config.allowed_roots,
            log_level=config.log_level,
        )
    raise SystemExit(asyncio.run(run_live_eval(config, strict_ocr=args.strict_ocr)))


if __name__ == "__main__":
    main()

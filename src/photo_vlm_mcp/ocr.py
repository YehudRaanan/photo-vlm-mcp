from __future__ import annotations

from io import BytesIO

from PIL import Image

from photo_vlm_mcp.config import Config
from photo_vlm_mcp.errors import PhotoVlmError
from photo_vlm_mcp.images import PhotoInput
from photo_vlm_mcp.ollama import OllamaClient
from photo_vlm_mcp.prompts import photo_ocr_prompt


async def run_photo_ocr(
    config: Config,
    ollama: OllamaClient,
    photo: PhotoInput,
    *,
    engine: str,
    model: str | None,
    structured: bool,
    language: str | None,
) -> dict[str, object]:
    if engine == "vlm":
        selected = model or config.ocr_model
        result = await ollama.chat(
            model=selected,
            prompt=photo_ocr_prompt(structured=structured, language=language),
            images_b64=[photo.base64],
            temperature=0.0,
        )
        return {
            "text": result.text,
            "format": "markdown" if structured else "plain",
            "engine": "vlm",
            "model": result.model,
            "latency_ms": result.latency_ms,
        }
    if engine == "tesseract":
        return _run_tesseract(photo, structured=structured, language=language)
    raise PhotoVlmError("engine must be 'vlm' or 'tesseract'.")


def _run_tesseract(
    photo: PhotoInput, *, structured: bool, language: str | None
) -> dict[str, object]:
    try:
        import pytesseract
    except ImportError as exc:
        raise PhotoVlmError(
            "engine:'tesseract' requires the tesseract binary and pytesseract; "
            "use engine:'vlm' for photographed text."
        ) from exc
    image = Image.open(BytesIO(photo.data))
    config = "--psm 6" if structured else ""
    text = pytesseract.image_to_string(image, lang=language, config=config)
    return {
        "text": text,
        "format": "markdown" if structured else "plain",
        "engine": "tesseract",
        "model": None,
        "latency_ms": 0,
    }

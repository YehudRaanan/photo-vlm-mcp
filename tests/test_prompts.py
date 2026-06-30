from photo_vlm_mcp.prompts import (
    compare_photos_prompt,
    inspect_scene_prompt,
    photo_ocr_prompt,
)


def test_photo_ocr_prompt_marks_uncertainty():
    prompt = photo_ocr_prompt(structured=True, language="eng")

    assert "Transcribe all visible text exactly" in prompt
    assert "[?]" in prompt
    assert "markdown" in prompt


def test_inspect_scene_prompt_requests_json():
    prompt = inspect_scene_prompt(focus="product label", include_uncertainty=True)

    assert "compact JSON" in prompt
    assert "product label" in prompt
    assert "uncertainties" in prompt


def test_compare_prompt_mentions_differences():
    assert "differences" in compare_photos_prompt(None, "brief")

from photo_vlm_mcp.config import Config


def test_config_uses_photo_specific_env(monkeypatch):
    monkeypatch.setenv("PHOTO_VLM_MODEL", "model-a")
    monkeypatch.setenv("PHOTO_OCR_MODEL", "model-b")

    cfg = Config.from_env()

    assert cfg.photo_model == "model-a"
    assert cfg.ocr_model == "model-b"


def test_config_accepts_legacy_alias(monkeypatch):
    monkeypatch.delenv("PHOTO_VLM_MODEL", raising=False)
    monkeypatch.setenv("VLM_MODEL", "legacy-model")

    assert Config.from_env().photo_model == "legacy-model"

from __future__ import annotations

import json

from photo_vlm_mcp import __version__
from photo_vlm_mcp.cli import main


def test_cli_version(capsys):
    main(["--version"])

    assert capsys.readouterr().out.strip() == __version__


def test_cli_print_config(capsys, monkeypatch):
    monkeypatch.setenv("PHOTO_VLM_MODEL", "photo-model")

    main(["--print-config"])

    data = json.loads(capsys.readouterr().out)
    assert data["photo_model"] == "photo-model"

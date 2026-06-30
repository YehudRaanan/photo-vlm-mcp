from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from photo_vlm_mcp import __version__
from photo_vlm_mcp.config import Config


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Local Ollama-backed MCP server for photo understanding."
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print effective non-secret config as JSON and exit.",
    )
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return
    if args.print_config:
        cfg = Config.from_env()
        data = asdict(cfg)
        data["allowed_roots"] = [str(path) for path in cfg.allowed_roots]
        print(json.dumps(data, indent=2))
        return

    from photo_vlm_mcp.server import run_server

    run_server()

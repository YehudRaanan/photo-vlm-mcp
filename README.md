# photo-vlm-mcp

`photo-vlm-mcp` is a local, Ollama-backed MCP server that gives coding assistants a
portable photo-understanding toolset:

- `analyze_photo` - ask questions about a real-world photo.
- `photo_ocr` - extract text from labels, receipts, whiteboards, signs, and photographed pages.
- `inspect_scene` - return structured objects, scene context, visible text, quality, and uncertainty.
- `compare_photos` - compare before/after or near-duplicate photos.
- `extract_metadata` - read dimensions, orientation, EXIF fields, GPS, and optional SHA-256.
- `health` - check Ollama reachability and configured model availability.

It is designed for user-level registration with Claude Code, Codex, Antigravity, Cursor,
Cline, Windsurf, Zed, and other MCP clients.

## Requirements

- Python 3.11+
- Ollama running locally
- A vision-capable Ollama model

Recommended local models:

```powershell
ollama pull qwen3-vl:8b
ollama pull minicpm-v
```

If `qwen3-vl:8b` is unavailable in your Ollama build, use `qwen2.5vl:7b` or another
vision model from `ollama.com/search?c=vision`.

## Install

From source:

```powershell
git clone https://github.com/photo-vlm-mcp/photo-vlm-mcp.git
cd photo-vlm-mcp
python -m pip install -e .
```

With optional Tesseract OCR support:

```powershell
python -m pip install -e ".[tesseract]"
```

## Run

```powershell
photo-vlm-mcp
```

The server uses MCP over stdio, so it normally runs under an MCP client rather than
as a long-lived terminal command.

Helpful local checks:

```powershell
photo-vlm-mcp --version
photo-vlm-mcp --print-config
```

## Register With Claude Code

```powershell
claude mcp add photo-vlm --scope user -- photo-vlm-mcp
```

With explicit model config:

```powershell
claude mcp add photo-vlm --scope user `
  -e OLLAMA_URL=http://127.0.0.1:11434 `
  -e PHOTO_VLM_MODEL=qwen3-vl:8b `
  -e PHOTO_OCR_MODEL=minicpm-v `
  -- photo-vlm-mcp
```

## Register With Codex / Antigravity / Other MCP Clients

Add this server to the client user-level MCP config:

```json
{
  "mcpServers": {
    "photo-vlm": {
      "command": "photo-vlm-mcp",
      "env": {
        "OLLAMA_URL": "http://127.0.0.1:11434",
        "PHOTO_VLM_MODEL": "qwen3-vl:8b",
        "PHOTO_OCR_MODEL": "minicpm-v"
      }
    }
  }
}
```

If the console script is not on PATH, use:

```json
{
  "command": "python",
  "args": ["-m", "photo_vlm_mcp"]
}
```

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama endpoint |
| `PHOTO_VLM_MODEL` | `qwen3-vl:8b` | Model for analysis, scene inspection, comparison |
| `PHOTO_OCR_MODEL` | `minicpm-v` | Model for VLM OCR |
| `PHOTO_VLM_MAX_TOKENS` | `1024` | Default generation limit |
| `PHOTO_VLM_TIMEOUT` | `120` | Ollama request timeout in seconds |
| `PHOTO_VLM_KEEP_ALIVE` | `10m` | Ollama keep-alive setting |
| `PHOTO_VLM_MAX_DIM` | `2048` | Downscale longest side before inference |
| `PHOTO_VLM_MAX_IMAGE_MB` | `20` | Reject larger images |
| `PHOTO_VLM_FETCH_TIMEOUT` | `15` | URL fetch timeout |
| `PHOTO_VLM_ALLOW_PRIVATE_URLS` | `0` | Allow private/loopback URLs |
| `PHOTO_VLM_ALLOWED_ROOTS` | unset | Optional path allow-list, separated by `;` on Windows or `:` elsewhere |

Legacy aliases `VLM_MODEL`, `OCR_MODEL`, and related `VLM_*` variables are also accepted.

## QA

```powershell
python -m pytest
python -m ruff check src tests scripts
python -m black --check src tests scripts
python -m isort --check-only src tests scripts
```

The unit tests mock Ollama and validate image input handling, metadata extraction, prompt
construction, and client behavior. Live model quality evaluation belongs in a separate
environment with Ollama and selected models installed.

See also:

- [Client setup](docs/clients.md)
- [Evaluation](docs/evaluation.md)
- [Release checklist](docs/release.md)

## License

MIT

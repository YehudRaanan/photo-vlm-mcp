# Client Setup

This server uses MCP over stdio and is intentionally client-neutral.

## Claude Code

```powershell
claude mcp add photo-vlm --scope user -- photo-vlm-mcp
```

Or without installing the console script:

```powershell
claude mcp add photo-vlm --scope user -- python -m photo_vlm_mcp
```

## Codex

Add the server to your user-level MCP configuration:

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

If `photo-vlm-mcp` is not on PATH:

```json
{
  "mcpServers": {
    "photo-vlm": {
      "command": "python",
      "args": ["-m", "photo_vlm_mcp"]
    }
  }
}
```

## Antigravity

Use the same MCP server definition as Codex:

```json
{
  "mcpServers": {
    "photo-vlm": {
      "command": "photo-vlm-mcp"
    }
  }
}
```

If Antigravity exposes separate user and project MCP scopes, prefer user scope for this
server because the Ollama daemon and model cache are machine-level resources.

## Suggested User Rule

```markdown
When a real-world photo is provided and precise visual reading matters, use the
`photo-vlm` MCP server before relying only on native vision. Use `analyze_photo`
for general questions, `photo_ocr` for labels/signs/receipts/whiteboards/pages,
`inspect_scene` for objects and conditions, `compare_photos` for before/after
checks, and `extract_metadata` only when capture metadata matters.
```

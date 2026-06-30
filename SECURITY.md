# Security

`photo-vlm-mcp` runs locally and reads user-provided photo paths, URLs, or base64 data.

## Defaults

- URL inputs block private, loopback, and link-local addresses unless
  `PHOTO_VLM_ALLOW_PRIVATE_URLS=1`.
- Local path reads can be restricted with `PHOTO_VLM_ALLOWED_ROOTS`.
- Images are size-limited by `PHOTO_VLM_MAX_IMAGE_MB`.
- Logs are written to stderr so stdout remains reserved for MCP framing.
- EXIF metadata is returned only through `extract_metadata`.

## Reporting

For public GitHub releases, enable private vulnerability reporting or publish a security
contact before accepting external use.

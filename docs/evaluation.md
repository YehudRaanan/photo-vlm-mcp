# Evaluation

The project has two QA layers.

## 1. Deterministic Unit QA

Run this on every commit:

```powershell
python -m pytest
python -m ruff check src tests scripts
python -m black --check src tests scripts
python -m isort --check-only src tests scripts
```

This covers:

- image input validation
- base64 data URI handling
- metadata and hashing
- prompt construction
- Ollama client request shape
- config/env behavior

## 2. Live Ollama Evaluation

Live evaluation needs local Ollama and pulled vision models. It is intentionally separate
from CI so public contributors can run tests without a GPU.

```powershell
python scripts/evaluate.py
```

The live evaluator checks:

- `health` can reach Ollama
- configured models are listed
- `analyze_photo` returns non-empty output for a generated photo-like fixture
- `photo_ocr` returns text containing the expected synthetic label
- `extract_metadata` returns dimensions and hash

Model quality is hardware/model dependent. Treat evaluation output as a regression signal,
not as a universal benchmark.

Use explicit local models when the recommended defaults are not installed:

```powershell
python scripts/evaluate.py --photo-model llava:7b --ocr-model llava:7b
```

By default, OCR mismatch is reported as a warning because weaker local models can fail the
synthetic OCR fixture. For release validation with a recommended OCR model, make it strict:

```powershell
python scripts/evaluate.py --strict-ocr
```

# Contributing

## Local Setup

```powershell
python -m pip install -e ".[dev]"
```

## Required Checks

```powershell
python -m pytest
python -m ruff check src tests scripts
python -m black --check src tests scripts
python -m isort --check-only src tests scripts
```

## Live Evaluation

Live model evaluation is optional for routine contributions because it requires Ollama,
local model downloads, and suitable hardware:

```powershell
python scripts/evaluate.py
```

If a change affects prompt templates, Ollama request construction, image preprocessing,
or OCR behavior, include live evaluation output in the pull request when feasible.

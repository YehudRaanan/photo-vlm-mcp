$ErrorActionPreference = "Stop"

python -m pytest
python -m ruff check src tests scripts
python -m black --check src tests scripts
python -m isort --check-only src tests scripts

Write-Host "QA passed."

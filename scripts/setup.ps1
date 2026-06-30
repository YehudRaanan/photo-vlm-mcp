param(
  [string]$PhotoModel = $env:PHOTO_VLM_MODEL,
  [string]$OcrModel = $env:PHOTO_OCR_MODEL
)

if (-not $PhotoModel) { $PhotoModel = "qwen3-vl:8b" }
if (-not $OcrModel) { $OcrModel = "minicpm-v" }

ollama list | Out-Host

foreach ($model in @($PhotoModel, $OcrModel) | Select-Object -Unique) {
  if (-not (ollama list | Select-String -SimpleMatch $model)) {
    Write-Host "Pulling missing model: $model"
    ollama pull $model
  }
}

Write-Host "Setup complete."

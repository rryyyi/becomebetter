param([string]$ModelDir = (Join-Path $PSScriptRoot "..\models\gguf"))

$ErrorActionPreference = "Stop"
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$ModelDir = [IO.Path]::GetFullPath($ModelDir)
$python = Join-Path $root ".venv\Scripts\python.exe"
$textModel = Join-Path $ModelDir "Mistral-7B-Instruct-v0.2-Q4_K_M.gguf"
$visionModel = Join-Path $ModelDir "Pixtral-12B-2409-Q4_K_M.gguf"
$mmproj = Join-Path $ModelDir "mmproj-Pixtral-12B-2409-f16.gguf"
foreach ($path in @($python, $textModel, $visionModel, $mmproj)) { if (-not (Test-Path $path)) { throw "Required file not found: $path. Run setup_model_services.ps1 first." } }

Start-Process -FilePath $python -WorkingDirectory $root -ArgumentList @("-m", "llama_cpp.server", "--model", $textModel, "--host", "127.0.0.1", "--port", "8080", "--n_ctx", "4096") | Out-Null
Start-Process -FilePath $python -WorkingDirectory $root -ArgumentList @("-m", "llama_cpp.server", "--model", $visionModel, "--chat_format", "chatml", "--clip_model_path", $mmproj, "--host", "127.0.0.1", "--port", "8081", "--n_ctx", "4096") | Out-Null
Write-Host "STE listening on http://127.0.0.1:8080"
Write-Host "SGE listening on http://127.0.0.1:8081"

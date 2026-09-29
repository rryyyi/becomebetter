param(
    [string]$InstallDir = (Join-Path $PSScriptRoot "..\runtime"),
    [string]$ModelDir = (Join-Path $PSScriptRoot "..\models\gguf")
)

$ErrorActionPreference = "Stop"
$InstallDir = [IO.Path]::GetFullPath($InstallDir)
$ModelDir = [IO.Path]::GetFullPath($ModelDir)
New-Item -ItemType Directory -Force $InstallDir, $ModelDir | Out-Null

Write-Host "Installing the OpenAI-compatible llama.cpp Python server..."
$venvPython = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) { throw "Project virtual environment not found. Create .venv first." }
& $venvPython -m pip install --upgrade llama-cpp-python huggingface_hub

Write-Host "Downloading Mistral-7B and Pixtral-12B GGUF models..."
& $venvPython -m huggingface_hub.commands.huggingface_cli download bartowski/Mistral-7B-Instruct-v0.2-GGUF Mistral-7B-Instruct-v0.2-Q4_K_M.gguf --local-dir $ModelDir --local-dir-use-symlinks False
& $venvPython -m huggingface_hub.commands.huggingface_cli download bartowski/Pixtral-12B-2409-GGUF Pixtral-12B-2409-Q4_K_M.gguf mmproj-Pixtral-12B-2409-f16.gguf --local-dir $ModelDir --local-dir-use-symlinks False

Write-Host "Model setup complete. Files are in $ModelDir"

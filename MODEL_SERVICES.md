# Local Model Services

The application expects two OpenAI-compatible local endpoints:

- STE: `http://127.0.0.1:8080/v1/chat/completions` using Mistral-7B
- SGE: `http://127.0.0.1:8081/v1/chat/completions` using Pixtral-12B

The GGUF files are intentionally kept out of Git because they are several gigabytes each. From the repository root, run:

```powershell
.\scripts\setup_model_services.ps1
.\scripts\start_model_services.ps1
```

Setup installs `llama-cpp-python` into `.venv` and downloads Q4_K_M models from Hugging Face, including the Pixtral vision projector.

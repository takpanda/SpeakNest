# Whisper STT Service

FastAPI service using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) with GGML medium model.

## Endpoints

- `GET /health` — Health check (includes model load status)
- `POST /transcribe` — Transcribe uploaded audio file
  - Form fields: `file` (required), `model` (optional), `language` (optional)
  - Response: `{"text": "...", "language_detected": "..."}`
- `GET /models` — List available model info

## Build & Run

```bash
docker compose up --build whisper
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `medium` | GGML model size |

## Notes

- First startup downloads ~1.5 GB model from Hugging Face
- Healthcheck start period is 300s to accommodate model download
- Uses `int8` quantization for memory efficiency on CPU

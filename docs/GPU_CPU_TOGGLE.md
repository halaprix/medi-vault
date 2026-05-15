# GPU vs CPU Toggle

## Ollama

By default uses CPU. For GPU acceleration:

```bash
# In docker-compose.yml, add under ollama service:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## OCR (PaddleOCR)

PaddleOCR detects GPU availability automatically. Set environment variable:

```env
PADDLE_DEVICE=gpu  # or cpu
```

Without GPU, services fall back to CPU — slower but functional.

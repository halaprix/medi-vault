# Troubleshooting

## Docker Issues

### Services won't start
```bash
docker compose down -v
docker compose up -d
```

### Database connection errors
Check that PostgreSQL is healthy:
```bash
docker compose ps postgres
docker compose logs postgres
```

## OCR Issues

### Tesseract/PaddleOCR not found
The OCR service falls back gracefully. Ensure the `celery_worker` service has the correct image.

## LLM Issues

### Ollama not responding
```bash
docker compose logs ollama
# Pull model manually:
docker compose exec ollama ollama pull llama3.2
```

## Frontend Issues

### Blank page
```bash
docker compose logs frontend
# Check for build errors
cd apps/frontend && npm run build
```

## Data Recovery

Your data is stored in the PostgreSQL volume. Back it up:
```bash
docker compose exec postgres pg_dump -U medi_vault > backup.sql
```

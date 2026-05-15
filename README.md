# medi-vault

Your personal health data vault. Upload medical test results, track biomarkers over time, and get AI-powered insights — all local and private.

## Quick Start

```bash
cp .env.example .env
docker compose up -d
```

Then visit `http://localhost:3005`.

## Architecture

- **Backend**: FastAPI (Python) — REST API + async task processing
- **Frontend**: Next.js 14 (TypeScript) — App Router + Tailwind CSS
- **Database**: PostgreSQL — encrypted health data storage
- **Vector DB**: ChromaDB — medical knowledge retrieval (RAG)
- **LLM**: Ollama — local document parsing (no data leaves your machine)
- **OCR**: PaddleOCR / DocTR — extract text from PDF/image lab results

## Features

- Upload PDF/image lab results → automatic OCR + LLM extraction
- Track 80+ biomarkers with reference ranges
- Trend visualization (weight, cholesterol, glucose, etc.)
- Google Fit sync (weight, steps, sleep, heart rate)
- RAG-powered health recommendations based on medical guidelines
- Full encryption at rest (Fernet)
- PIN-protected local access

## Development

```bash
make up          # Start all services
make migrate     # Run database migrations
make seed        # Load biomarker reference data
make ingest-rag  # Populate knowledge base into ChromaDB
make test        # Run all tests
```

## License

MIT

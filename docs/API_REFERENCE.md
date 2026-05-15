# API Reference (auto-generated)

See Swagger UI at `http://localhost:8000/docs` for interactive API documentation.

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/setup` | First-run PIN setup |
| POST | `/api/v1/auth/login` | Login with PIN |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/status` | Auth status |

## Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload PDF/image |
| GET | `/api/v1/documents/` | List documents |
| GET | `/api/v1/documents/{id}` | Get document |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/documents/{id}/reprocess` | Re-run OCR+LLM |

## Health Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/metrics/` | List metrics |
| POST | `/api/v1/metrics/` | Add metric |
| DELETE | `/api/v1/metrics/{id}` | Delete metric |
| GET | `/api/v1/metrics/summary` | Summary view |

## Google Fit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/google/connect` | Start OAuth |
| GET | `/api/v1/auth/google/callback` | OAuth callback |
| GET | `/api/v1/auth/google/status` | Connection status |
| DELETE | `/api/v1/auth/google/disconnect` | Disconnect |
| POST | `/api/v1/sync/trigger` | Manual sync |
| GET | `/api/v1/sync/jobs` | Sync job history |

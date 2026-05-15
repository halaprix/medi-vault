# ADR 002: Use ChromaDB for RAG Knowledge Base

**Status**: Accepted
**Date**: 2026-05-14

## Decision
ChromaDB for vector storage and retrieval.

## Rationale
- Lightweight, runs in Docker alongside other services
- Simple API (no separate vector DB cluster)
- Sufficient for medical guideline retrieval (hundreds of documents, not millions)
- Integrates well with Ollama embeddings

## Alternatives Considered
- **Pinecone**: Cloud-only, violates local-first principle
- **Qdrant**: More features but heavier deployment
- **FAISS**: File-based, harder to update incrementally

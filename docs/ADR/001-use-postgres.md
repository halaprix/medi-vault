# ADR 001: Use PostgreSQL as Primary Database

**Status**: Accepted
**Date**: 2026-05-14

## Context
Need a database for structured health data: users, documents, test results, biomarkers, health metrics, recommendations.

## Decision
PostgreSQL.

## Rationale
- Strong relational model for medical data
- JSONB for flexible biomarker metadata
- Full-text search for document content
- Mature ecosystem (SQLAlchemy, Alembic)
- Runs locally in Docker

## Alternatives Considered
- **SQLite**: Too limited for concurrent access (async workers)
- **MongoDB**: Schema flexibility but weaker integrity guarantees for medical data
- **MySQL**: PostgreSQL has better JSON support and async drivers

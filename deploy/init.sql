-- GOTHAM INDIA — database bootstrap (extensions only; schema is owned by Alembic)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- trigram index support for fuzzy record search
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector: reserved for the embedding-backed retriever

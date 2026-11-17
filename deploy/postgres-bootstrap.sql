-- GOTHAM INDIA — PostgreSQL bootstrap (run once as a superuser / DBA role).
-- Application roles must NOT be superusers; extensions are provisioned here, not at runtime.

CREATE ROLE gotham LOGIN PASSWORD :'gotham_password';
CREATE DATABASE gotham OWNER gotham;
\connect gotham

CREATE EXTENSION IF NOT EXISTS postgis;    -- administrative geography, spatial predicates
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- trigram similarity for entity resolution blocking
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector: embedding-backed retrieval
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid(), digest() for audit hash chain

GRANT ALL ON SCHEMA public TO gotham;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table storing each chunk that will be embedded (summary/interest/property)
CREATE TABLE IF NOT EXISTS major_vector_chunks (
    id BIGSERIAL PRIMARY KEY,
    major_seq TEXT NOT NULL,
    major TEXT NOT NULL,
    salary TEXT,
    employment TEXT,
    job TEXT,
    qualifications TEXT,
    chunk_field TEXT NOT NULL,
    chunk_index INT NOT NULL DEFAULT 0,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(3072) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prevent duplicate chunks per major
CREATE UNIQUE INDEX IF NOT EXISTS uq_major_chunk
    ON major_vector_chunks (major_seq, chunk_field, chunk_index);

CREATE TABLE IF NOT EXISTS major_universities (
    id BIGSERIAL PRIMARY KEY,
    major_seq TEXT NOT NULL,
    school_name TEXT NOT NULL,
    major_name TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_major_universities
    ON major_universities (major_seq, school_name, major_name);

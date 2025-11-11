-- file: vector_init.sql
-- Purpose: Initialize pgvector with separated meta_df and vector indexes

-- 1) Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2) Create dedicated schema
CREATE SCHEMA IF NOT EXISTS qa;

-- ============================================
-- META TABLE: meta_df (표시/필터용)
-- ============================================
CREATE TABLE IF NOT EXISTS qa.meta_df (
    chunk_id VARCHAR(100) PRIMARY KEY,
    doc_id INTEGER NOT NULL,                              -- sample_id
    occupation VARCHAR(50),
    gender VARCHAR(20),
    age_range VARCHAR(20),
    experience VARCHAR(20),
    answer_intent_category VARCHAR(100),
    answer_emotion_expression VARCHAR(100),
    answer_emotion_category VARCHAR(50),
    question_intent VARCHAR(100),
    question_text TEXT NOT NULL,
    question_text_norm TEXT,                              -- 소문자/공백정규화/기호제거
    answer_text TEXT NOT NULL,
    content_combined TEXT NOT NULL,                       -- Q: {question_text}\nA: {answer_text}
    tokens_answer INTEGER,
    tokens_combined INTEGER,
    group_id VARCHAR(100),                                -- 같은 질문에 대한 다수 답변 묶기용
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- VECTOR TABLE: vec_q_index (질문 전용 Q-Index)
-- ============================================
CREATE TABLE IF NOT EXISTS qa.vec_q_index (
    chunk_id_q VARCHAR(100) PRIMARY KEY,
    chunk_id VARCHAR(100) NOT NULL,                       -- FK to meta_df
    emb_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    emb_dim INTEGER NOT NULL DEFAULT 3072,
    embedding vector(3072) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chunk_id) REFERENCES qa.meta_df(chunk_id) ON DELETE CASCADE
);

-- ============================================
-- VECTOR TABLE: vec_a_index (답변/청킹 본문 전용 A-Index)
-- ============================================
CREATE TABLE IF NOT EXISTS qa.vec_a_index (
    id BIGSERIAL PRIMARY KEY,
    chunk_id VARCHAR(100) NOT NULL,                       -- FK to meta_df
    emb_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    emb_dim INTEGER NOT NULL DEFAULT 3072,
    embedding vector(3072) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chunk_id) REFERENCES qa.meta_df(chunk_id) ON DELETE CASCADE
);

-- ============================================
-- VECTOR INDEXES: Disabled for 3072 dimensions
-- Note: Both ivfflat and hnsw support max 2000 dimensions
-- For 3072 dimensions, indexes are not supported by pgvector
-- Queries will work but may be slower without indexes
-- Consider reducing embedding dimensions to 2000 or less for better performance
-- ============================================

-- Q-Index: 질문 임베딩 검색용 (DISABLED - 3072 dimensions exceed limit)
-- CREATE INDEX IF NOT EXISTS vec_q_index_embedding_idx
-- ON qa.vec_q_index
-- USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);

-- A-Index: 답변 임베딩 검색용 (DISABLED - 3072 dimensions exceed limit)
-- CREATE INDEX IF NOT EXISTS vec_a_index_embedding_idx
-- ON qa.vec_a_index
-- USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);

-- ============================================
-- METADATA INDEXES: Filtering and joins
-- ============================================

-- Primary filters
CREATE INDEX IF NOT EXISTS idx_meta_doc_id ON qa.meta_df(doc_id);
CREATE INDEX IF NOT EXISTS idx_meta_occupation ON qa.meta_df(occupation);
CREATE INDEX IF NOT EXISTS idx_meta_question_intent ON qa.meta_df(question_intent);
CREATE INDEX IF NOT EXISTS idx_meta_answer_intent ON qa.meta_df(answer_intent_category);
CREATE INDEX IF NOT EXISTS idx_meta_group_id ON qa.meta_df(group_id);
CREATE INDEX IF NOT EXISTS idx_meta_emotion ON qa.meta_df(answer_emotion_category);

-- Foreign key indexes for efficient joins
CREATE INDEX IF NOT EXISTS idx_vec_q_chunk_id ON qa.vec_q_index(chunk_id);
CREATE INDEX IF NOT EXISTS idx_vec_a_chunk_id ON qa.vec_a_index(chunk_id);

-- ============================================
-- PERMISSIONS
-- ============================================
-- Grant permissions to skn4th user (or create interview_user if needed)
GRANT USAGE ON SCHEMA qa TO skn4th;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA qa TO skn4th;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA qa TO skn4th;

-- ============================================
-- RUNTIME SETTINGS (set per-session in app)
-- ============================================
-- For HNSW indexes, use: SET hnsw.ef_search = 40;  -- tune based on recall requirements (20~100)

-- file: meta_queries.sql
-- Purpose: Helper functions for separated meta_df and vector indexes

-- ============================================
-- 1) Upsert metadata
-- ============================================
CREATE OR REPLACE FUNCTION qa.upsert_metadata(
    p_chunk_id                  VARCHAR(100),
    p_doc_id                    INTEGER,
    p_occupation                VARCHAR(50),
    p_gender                    VARCHAR(20),
    p_age_range                 VARCHAR(20),
    p_experience                VARCHAR(20),
    p_answer_intent_category    VARCHAR(100),
    p_answer_emotion_expression VARCHAR(100),
    p_answer_emotion_category   VARCHAR(50),
    p_question_intent           VARCHAR(100),
    p_question_text             TEXT,
    p_question_text_norm        TEXT,
    p_answer_text               TEXT,
    p_content_combined          TEXT,
    p_tokens_answer             INTEGER,
    p_tokens_combined           INTEGER,
    p_group_id                  VARCHAR(100)
) RETURNS qa.meta_df AS $$
DECLARE
    v_row qa.meta_df;
BEGIN
    INSERT INTO qa.meta_df (
        chunk_id, doc_id, occupation, gender, age_range, experience,
        answer_intent_category, answer_emotion_expression, answer_emotion_category,
        question_intent, question_text, question_text_norm, answer_text,
        content_combined, tokens_answer, tokens_combined, group_id
    ) VALUES (
        p_chunk_id, p_doc_id, p_occupation, p_gender, p_age_range, p_experience,
        p_answer_intent_category, p_answer_emotion_expression, p_answer_emotion_category,
        p_question_intent, p_question_text, p_question_text_norm, p_answer_text,
        p_content_combined, p_tokens_answer, p_tokens_combined, p_group_id
    )
    ON CONFLICT (chunk_id) DO UPDATE SET
        occupation                 = EXCLUDED.occupation,
        gender                     = EXCLUDED.gender,
        age_range                  = EXCLUDED.age_range,
        experience                 = EXCLUDED.experience,
        answer_intent_category     = EXCLUDED.answer_intent_category,
        answer_emotion_expression  = EXCLUDED.answer_emotion_expression,
        answer_emotion_category    = EXCLUDED.answer_emotion_category,
        question_intent            = EXCLUDED.question_intent,
        question_text              = EXCLUDED.question_text,
        question_text_norm         = EXCLUDED.question_text_norm,
        answer_text                = EXCLUDED.answer_text,
        content_combined           = EXCLUDED.content_combined,
        tokens_answer              = EXCLUDED.tokens_answer,
        tokens_combined            = EXCLUDED.tokens_combined,
        group_id                   = EXCLUDED.group_id
    RETURNING * INTO v_row;
    RETURN v_row;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 2) Upsert Q-Index embedding
-- ============================================
CREATE OR REPLACE FUNCTION qa.upsert_q_embedding(
    p_chunk_id_q  VARCHAR(100),
    p_chunk_id    VARCHAR(100),
    p_emb_model   VARCHAR(100),
    p_emb_dim     INTEGER,
    p_embedding   vector(3072)
) RETURNS qa.vec_q_index AS $$
DECLARE
    v_row qa.vec_q_index;
BEGIN
    INSERT INTO qa.vec_q_index (chunk_id_q, chunk_id, emb_model, emb_dim, embedding)
    VALUES (p_chunk_id_q, p_chunk_id, p_emb_model, p_emb_dim, p_embedding)
    ON CONFLICT (chunk_id_q) DO UPDATE SET
        embedding = EXCLUDED.embedding,
        emb_model = EXCLUDED.emb_model,
        emb_dim   = EXCLUDED.emb_dim
    RETURNING * INTO v_row;
    RETURN v_row;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 3) Insert A-Index embedding (multiple chunks per doc)
-- ============================================
CREATE OR REPLACE FUNCTION qa.insert_a_embedding(
    p_chunk_id   VARCHAR(100),
    p_emb_model  VARCHAR(100),
    p_emb_dim    INTEGER,
    p_embedding  vector(3072)
) RETURNS qa.vec_a_index AS $$
DECLARE
    v_row qa.vec_a_index;
BEGIN
    INSERT INTO qa.vec_a_index (chunk_id, emb_model, emb_dim, embedding)
    VALUES (p_chunk_id, p_emb_model, p_emb_dim, p_embedding)
    RETURNING * INTO v_row;
    RETURN v_row;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 4) Search Q-Index with metadata filters
-- ============================================
CREATE OR REPLACE FUNCTION qa.search_questions(
    p_query_vec   vector(3072),
    p_k           INTEGER DEFAULT 10,
    p_occupation  VARCHAR DEFAULT NULL,
    p_q_intent    VARCHAR DEFAULT NULL
) RETURNS TABLE (
    chunk_id            VARCHAR(100),
    doc_id              INTEGER,
    question_text       TEXT,
    answer_text         TEXT,
    similarity          DOUBLE PRECISION,
    occupation          VARCHAR(50),
    question_intent     VARCHAR(100),
    answer_intent       VARCHAR(100)
) AS $$
    SELECT
        m.chunk_id,
        m.doc_id,
        m.question_text,
        m.answer_text,
        1 - (q.embedding <=> p_query_vec) AS similarity,
        m.occupation,
        m.question_intent,
        m.answer_intent_category
    FROM qa.vec_q_index q
    JOIN qa.meta_df m ON q.chunk_id = m.chunk_id
    WHERE (p_occupation IS NULL OR m.occupation = p_occupation)
      AND (p_q_intent IS NULL OR m.question_intent = p_q_intent)
    ORDER BY q.embedding <-> p_query_vec
    LIMIT COALESCE(p_k, 10);
$$ LANGUAGE sql STABLE PARALLEL SAFE;

-- ============================================
-- 5) Search A-Index with metadata filters
-- ============================================
CREATE OR REPLACE FUNCTION qa.search_answers(
    p_query_vec   vector(3072),
    p_k           INTEGER DEFAULT 10,
    p_occupation  VARCHAR DEFAULT NULL,
    p_a_intent    VARCHAR DEFAULT NULL
) RETURNS TABLE (
    chunk_id            VARCHAR(100),
    doc_id              INTEGER,
    question_text       TEXT,
    answer_text         TEXT,
    content_combined    TEXT,
    similarity          DOUBLE PRECISION,
    occupation          VARCHAR(50),
    answer_intent       VARCHAR(100)
) AS $$
    SELECT
        m.chunk_id,
        m.doc_id,
        m.question_text,
        m.answer_text,
        m.content_combined,
        1 - (a.embedding <=> p_query_vec) AS similarity,
        m.occupation,
        m.answer_intent_category
    FROM qa.vec_a_index a
    JOIN qa.meta_df m ON a.chunk_id = m.chunk_id
    WHERE (p_occupation IS NULL OR m.occupation = p_occupation)
      AND (p_a_intent IS NULL OR m.answer_intent_category = p_a_intent)
    ORDER BY a.embedding <-> p_query_vec
    LIMIT COALESCE(p_k, 10);
$$ LANGUAGE sql STABLE PARALLEL SAFE;

-- ============================================
-- 6) Hybrid search (A + Q combined)
-- ============================================
CREATE OR REPLACE FUNCTION qa.search_hybrid(
    p_query_vec   vector(3072),
    p_k_total     INTEGER DEFAULT 10,
    p_k_q         INTEGER DEFAULT 3,  -- Q-Index results
    p_occupation  VARCHAR DEFAULT NULL
) RETURNS TABLE (
    chunk_id         VARCHAR(100),
    doc_id           INTEGER,
    question_text    TEXT,
    answer_text      TEXT,
    source_index     TEXT,  -- 'Q' or 'A'
    similarity       DOUBLE PRECISION,
    occupation       VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    WITH a_results AS (
        SELECT
            m.chunk_id, m.doc_id, m.question_text, m.answer_text,
            'A'::TEXT as source_index,
            1 - (a.embedding <=> p_query_vec) AS sim,
            m.occupation
        FROM qa.vec_a_index a
        JOIN qa.meta_df m ON a.chunk_id = m.chunk_id
        WHERE (p_occupation IS NULL OR m.occupation = p_occupation)
        ORDER BY a.embedding <-> p_query_vec
        LIMIT (p_k_total - p_k_q)
    ),
    q_results AS (
        SELECT
            m.chunk_id, m.doc_id, m.question_text, m.answer_text,
            'Q'::TEXT as source_index,
            1 - (q.embedding <=> p_query_vec) AS sim,
            m.occupation
        FROM qa.vec_q_index q
        JOIN qa.meta_df m ON q.chunk_id = m.chunk_id
        WHERE (p_occupation IS NULL OR m.occupation = p_occupation)
        ORDER BY q.embedding <-> p_query_vec
        LIMIT p_k_q
    )
    SELECT * FROM (
        SELECT * FROM a_results
        UNION ALL
        SELECT * FROM q_results
    ) combined
    ORDER BY combined.sim DESC
    LIMIT p_k_total;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================
-- 7) Utility: Stats check
-- ============================================
-- SELECT COUNT(*) as total_records FROM qa.meta_df;
-- SELECT COUNT(*) as q_embeddings FROM qa.vec_q_index;
-- SELECT COUNT(*) as a_embeddings FROM qa.vec_a_index;
-- SELECT occupation, COUNT(*) FROM qa.meta_df GROUP BY occupation ORDER BY COUNT(*) DESC;

-- ============================================
-- 8) Utility: Maintenance
-- ============================================
-- ANALYZE qa.meta_df;
-- ANALYZE qa.vec_q_index;
-- ANALYZE qa.vec_a_index;

-- ============================================
-- 9) Drop helpers (reset if needed)
-- ============================================
-- DROP TABLE IF EXISTS qa.vec_a_index CASCADE;
-- DROP TABLE IF EXISTS qa.vec_q_index CASCADE;
-- DROP TABLE IF EXISTS qa.meta_df CASCADE;

-- 1️⃣ pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 2️⃣ 테이블 생성 (임베딩 저장용)
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536)   -- ✅ OpenAI 등 임베딩 차원 수 맞추기
);

-- 3️⃣ 예시 데이터
INSERT INTO document_embeddings (content, embedding)
VALUES
('Hello world', '[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]'::vector);

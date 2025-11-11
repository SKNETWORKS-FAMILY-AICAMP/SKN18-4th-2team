-- 1️⃣ pgvector 확장 설치 (필수)
CREATE EXTENSION IF NOT EXISTS vector;

-------------------------------------------------------------
-- 2️⃣ 학과-대학 매핑 테이블 (RAG에서 사용할 메인 테이블)
-------------------------------------------------------------
CREATE TABLE IF NOT EXISTS university (
    id BIGSERIAL PRIMARY KEY,            -- 고유 ID
    school_name TEXT NOT NULL,           -- 대학 이름
    department TEXT NOT NULL,            -- 학과 이름
    category TEXT,                       -- 계열 (인문/이공/예체능 등)
    region TEXT,                         -- 지역
    description TEXT,                    -- 학과 설명 또는 요약
    program_features TEXT,               -- 프로그램/커리큘럼 특징
    employment_rate FLOAT,               -- 취업률
    avg_salary FLOAT,                    -- 평균 연봉
    admission_score TEXT,                -- 입시 점수대
    embedding VECTOR(3072) NOT NULL,     -- OpenAI Large Embedding (3072차원)
    metadata JSONB DEFAULT '{}'::jsonb,  -- 추가 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW() -- 생성 일시
);

-- 중복 방지: 같은 대학+학과는 1회만 등록
CREATE UNIQUE INDEX IF NOT EXISTS uq_university
    ON university (school_name, department);
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS majors (
    -- 메타데이터 (Metadata) --
    "majorSeq" INT PRIMARY KEY,
    major VARCHAR(255),
    salary FLOAT,
    employment VARCHAR(255),
    job TEXT,
    qualifications TEXT,
    universities TEXT,
    

    "text" TEXT,

    embedding vector(768) 
);

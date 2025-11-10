"""
pgvector 테이블 생성 및 배치 적재 유틸
"""
from typing import Any, Dict, List

from psycopg2 import sql
from psycopg2.extras import execute_values

TABLE_NAME = "majors"
VECTOR_DIMENSION = 1024  # multilingual-e5-large-instruct 출력 차원


def create_majors_table(conn):
    """
    pgvector를 사용하는 majors 테이블을 재생성합니다.
    """
    create_table_query = f"""
    DROP TABLE IF EXISTS {TABLE_NAME};

    CREATE TABLE {TABLE_NAME} (
        id SERIAL PRIMARY KEY,
        "majorSeq" INT,
        "chunkIndex" INT NOT NULL,
        major VARCHAR(255),
        salary FLOAT,
        employment VARCHAR(255),
        job TEXT,
        qualifications TEXT,
        universities TEXT,
        "text" TEXT,
        embedding vector({VECTOR_DIMENSION})
    );

    CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_majorSeq ON {TABLE_NAME}("majorSeq");
    """
    try:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
        conn.commit()
        print(f"테이블 '{TABLE_NAME}' (재)생성 완료. (Vector Dim: {VECTOR_DIMENSION})")
    except Exception as e:
        conn.rollback()
        print(f"테이블 생성 실패: {e}")
        raise


def insert_data_batch(conn, data_batch: List[Dict[str, Any]]):
    """
    데이터 배치를 받아 majors 테이블에 고속 INSERT 합니다.
    """
    if not data_batch:
        return 0

    columns = list(data_batch[0].keys())

    values = [
        tuple(
            item["embedding"] if col == "embedding" else item.get(col)
            for col in columns
        )
        for item in data_batch
    ]

    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
        sql.Identifier(TABLE_NAME),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )

    try:
        with conn.cursor() as cur:
            execute_values(cur, insert_query, values)
        conn.commit()
        return len(data_batch)
    except Exception as e:
        conn.rollback()
        print(f"데이터 배치 INSERT 실패: {e}")
        print("--- 실패한 데이터 샘플 (첫 번째) ---")
        print(data_batch[0])
        raise

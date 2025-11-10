# test_retrieval.py (multilingual-e5 버전)
import os

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# --- (1) 테스트 질문 ---
TEST_QUERY = "AI와 빅데이터를 배우는 학과가 있을까?"

# --- (2) 모델 이름 지정 ---
MODEL_NAME = "intfloat/multilingual-e5-large-instruct"
TABLE_NAME = "majors"
TOP_K = 5


def _format_query_for_model(query: str) -> str:
    cleaned = query.strip()
    if "e5" in MODEL_NAME.lower():
        return f"query: {cleaned}"
    return cleaned


def search_similar_majors(query: str):
    print(f"임베딩 모델 로드 중: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"질문 임베딩 중: \"{query}\"")
    query_embedding = model.encode(
        _format_query_for_model(query),
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    load_dotenv()
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            dbname=os.environ.get("POSTGRES_DB"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD"),
            port=os.environ.get("POSTGRES_PORT", 5432),
        )
        print("데이터베이스 연결 성공!")
        cur = conn.cursor()

        query_vector_str = str(query_embedding.tolist())

        query_sql = sql.SQL(
            """
            SELECT 
                major,
                "chunkIndex",
                "text",
                (embedding <=> %s) AS distance 
            FROM {}
            ORDER BY
                distance ASC
            LIMIT %s;
        """
        ).format(sql.Identifier(TABLE_NAME))

        cur.execute(query_sql, (query_vector_str, TOP_K))
        results = cur.fetchall()

        print("\n--- [검색 결과 (Cosine 거리 측정)] ---")

        for i, row in enumerate(results):
            major_name = row[0]
            chunk_index = row[1]
            text_value = row[2] or ""
            text_snippet = text_value[:80] + "..."
            distance = row[3]
            similarity = 1 - distance

            print(f"\n[순위 {i + 1}] 학과: {major_name} (chunk #{chunk_index})")
            print(f"  (Cosine 거리: {distance:.4f} / 유사도: {similarity:.4f})")
            print(f"  (본문 미리보기: {text_snippet})")

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    search_similar_majors(TEST_QUERY)

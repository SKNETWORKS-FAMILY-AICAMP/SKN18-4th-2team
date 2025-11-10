"""
RAG 벡터DB 빌드 파이프라인
(1. 데이터 로드 -> 2. 텍스트 가공 -> 3. 청크 분할 -> 4. 임베딩 -> 5. DB 적재)
"""
import time
from dotenv import load_dotenv

if not load_dotenv():
    print("경고: .env 파일을 찾지 못했습니다. 환경 변수를 직접 사용합니다.")


from tqdm import tqdm
from vectordb.db_manager import db_manager
from vectordb import data_loader
from vectordb import text_processor
from vectordb import embedder
from vectordb import pgvector_manager

##################
# 파이프라인 설정
#################
DATA_DIR = "backend/data"  # CSV 파일이 있는 위치
BATCH_SIZE = 64  # 배치 크기
MODEL_NAME = "intfloat/multilingual-e5-large-instruct"
EMBED_NORMALIZE = True
PARAGRAPHS_PER_CHUNK = 2  # 학과당 2문단 단위 청크


def main():
    start_total_time = time.time()
    total_inserted = 0

    try:
        # 1. 데이터 로드
        required_cols = list(text_processor.COLUMNS_TO_EMBED) + [
            "majorSeq",
            "major",
            "salary",
            "employment",
            "job",
            "qualifications",
            "universities",
        ]
        df = data_loader.load_major_data(DATA_DIR, required_columns=required_cols)

        # 2. 텍스트 생성
        df["text"] = text_processor.build_texts(df)

        # 3. 문단 청크 분할
        chunked_df = text_processor.chunk_dataframe(df, paragraphs_per_chunk=PARAGRAPHS_PER_CHUNK)

        # 4. 임베딩 모델 초기화
        rag_embedder = embedder.RAGEmbedder(model_name=MODEL_NAME)

        # 5. 테이블 재생성
        conn = db_manager.get_conn()
        pgvector_manager.create_majors_table(conn)
        db_manager.put_conn(conn)

        # 6. 임베딩 + DB 적재
        total_rows = len(chunked_df)
        print(f"\n--- 총 {total_rows}건 청크 임베딩 + DB 적재 작업 (배치 크기: {BATCH_SIZE}) ---")

        with tqdm(total=total_rows, desc="데이터 적재 진행") as pbar:
            for i in range(0, total_rows, BATCH_SIZE):
                batch_df = chunked_df.iloc[i : i + BATCH_SIZE]
                batch_texts = batch_df["text"].tolist()

                batch_embeddings = rag_embedder.embed_texts(
                    batch_texts,
                    batch_size=BATCH_SIZE,
                    normalize=EMBED_NORMALIZE,
                )

                batch_data_to_insert = []
                for idx, row in enumerate(batch_df.itertuples(index=False)):
                    record = {
                        "majorSeq": row.majorSeq,
                        "chunkIndex": int(row.chunkIndex),
                        "major": row.major,
                        "salary": row.salary,
                        "employment": row.employment,
                        "job": row.job,
                        "qualifications": row.qualifications,
                        "universities": row.universities,
                        "text": row.text,
                        "embedding": batch_embeddings[idx].tolist(),
                    }
                    batch_data_to_insert.append(record)

                conn = db_manager.get_conn()
                inserted_count = pgvector_manager.insert_data_batch(conn, batch_data_to_insert)
                db_manager.put_conn(conn)

                total_inserted += inserted_count
                pbar.update(inserted_count)

    except Exception as e:
        print("\n--- [치명적 오류] 파이프라인 중단 ---")
        print(f"오류: {e}")
        import traceback

        traceback.print_exc()

    finally:
        db_manager.close_all()

    end_total_time = time.time()
    print("\n--- RAG 벡터DB 구축 완료 ---")
    print(f"총 {total_inserted}건 레코드 적재 완료.")
    print(f"총 소요 시간: {end_total_time - start_total_time:.2f}초")


if __name__ == "__main__":
    main()

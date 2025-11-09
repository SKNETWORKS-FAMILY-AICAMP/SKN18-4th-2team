import os
import json
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import time

def load_data_to_pgvector(jsonl_file, table_name):
    """
    majors_embeddings.jsonl 파일을 읽어 pgvector DB에 적재합니다.
    """

    # 1. .env 파일에서 DB 접속 정보 로드
    load_dotenv()

    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"), # (docker-compose 외부 실행 시 'localhost')
            dbname=os.environ.get("POSTGRES_DB"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD"),
            port=os.environ.get("POSTGRES_PORT", 5432)
        )
        print("데이터베이스 연결 성공!")
    except psycopg2.OperationalError as e:
        print(f"데이터베이스 연결 실패: {e}")
        print("DB가 실행 중인지, .env 파일의 정보가 정확한지 확인하세요.")
        return

    cur = conn.cursor()

    start_time = time.time()
    insert_count = 0

    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)

                # 1. 컬럼명/값을 동적으로 구성 (jsonl의 모든 키)
                columns = record.keys()
                values = [
                    # (중요) pgvector는 Python 리스트를 "벡터 문자열"로 변환해줘야 합니다.
                    str(record['embedding']) if col == 'embedding' else record[col] 
                    for col in columns
                ]

                # 2. INSERT 쿼리 생성 (SQL Injection 방지)
                query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join(map(sql.Placeholder, columns))
                )

                # 3. 쿼리 실행
                cur.execute(query, record)
                insert_count += 1

        # 4. 트랜잭션 커밋
        conn.commit()

        end_time = time.time()
        print(f"\n--- 데이터 적재 완료! ---")
        print(f"총 {insert_count}개의 레코드를 {table_name} 테이블에 적재했습니다.")
        print(f"소요 시간: {end_time - start_time:.2f}초")

    except Exception as e:
        print(f"데이터 적재 중 오류 발생: {e}")
        conn.rollback() # 오류 발생 시 롤백
    finally:
        cur.close()
        conn.close()

# --- 메인 실행 ---
if __name__ == "__main__":
    if not os.path.exists('.env'):
        print("경고: .env 파일을 찾을 수 없습니다. DB 접속 정보를 환경변수에서 직접 읽습니다.")

    load_data_to_pgvector("majors_embeddings.jsonl", "majors")
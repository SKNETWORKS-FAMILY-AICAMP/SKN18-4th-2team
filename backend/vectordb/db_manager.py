"""

"""
# vectordb/db_manager.py
import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from pgvector.psycopg2 import register_vector  # <--- ★★★ 수정된 부분
from dotenv import load_dotenv

class DatabaseManager:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            load_dotenv()
            
            try:
                db_url = (
                    f"host={os.environ['POSTGRES_HOST']} "
                    f"port={os.environ['POSTGRES_PORT']} "
                    f"dbname={os.environ['POSTGRES_DB']} "
                    f"user={os.environ['POSTGRES_USER']} "
                    f"password={os.environ['POSTGRES_PASSWORD']}"
                )
                # 커넥션 풀 생성 (최소 1개, 최대 5개)
                cls._pool = SimpleConnectionPool(1, 5, dsn=db_url)
                print("DB 커넥션 풀 생성 성공.")
                
                # 풀의 모든 커넥션에 pgvector 확장 등록
                conn = None
                try:
                    conn = cls._pool.getconn()
                    register_vector(conn) # <--- 이제 이 함수를 올바르게 찾음
                    print("pgvector 확장(register_vector) 등록 완료.")
                finally:
                    if conn:
                        cls._pool.putconn(conn) # 사용 후 반환

            except Exception as e:
                print(f"DB 커넥션 풀 생성 실패: {e}")
                cls._instance = None
                raise
        return cls._instance

    def get_conn(self):
        """커넥션 풀에서 연결을 가져옵니다."""
        if self._pool is None:
            raise Exception("DB 커넥션 풀이 초기화되지 않았습니다.")
        return self._pool.getconn()

    def put_conn(self, conn):
        """연결을 풀에 반환합니다."""
        if self._pool is not None:
            self._pool.putconn(conn)

    def close_all(self):
        """모든 연결을 닫습니다."""
        if self._pool is not None:
            print("DB 커넥션 풀 닫는 중...")
            self._pool.closeall()
            DatabaseManager._pool = None
            DatabaseManager._instance = None

# 싱글톤 인스턴스 생성 (필요시 import db_manager.get_conn() 사용)
db_manager = DatabaseManager()
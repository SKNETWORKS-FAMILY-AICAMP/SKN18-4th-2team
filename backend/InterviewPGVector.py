from typing import Any, Dict, List, Optional, Tuple
import psycopg2

from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document


class InterviewPGVector(VectorStore):
    """면접 데이터용 PGVector 클래스 (interview.vector, interview.meta_df 테이블 사용)"""
    
    def __init__(self, conn_str: str, embedding_fn):
        self.conn_str = conn_str
        self.conn = psycopg2.connect(self.conn_str)
        self.embedding_fn = embedding_fn
    
    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding_fn,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        conn_str: Optional[str] = None,
        **kwargs,
    ) -> "InterviewPGVector":
        """클래스 메서드로 VectorStore 생성"""
        if conn_str is None:
            raise ValueError("conn_str is required")
        store = cls(conn_str=conn_str, embedding_fn=embedding_fn)
        return store
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """면접 데이터 추가 (현재는 미구현 - 별도 ingest 스크립트 사용)"""
        raise NotImplementedError("면접 데이터는 별도 ingest 스크립트로 적재하세요")
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """면접 데이터 유사도 검색 (메타데이터 필터링 지원)"""
        query_emb = self.embedding_fn.embed_query(query)
        params: List[Any] = []

        # 기본 쿼리: meta_df와 vector 조인
        sql_query = """
            SELECT 
                m.doc_id,
                m.occupation,
                m.gender,
                m.age_range,
                m.experience,
                m.question_intent,
                m.answer_intent_category,
                m.answer_emotion_category,
                m.question_text,
                m.answer_text,
                m.content_combined,
                v.chunk_id,
                v.chunk_seq
            FROM interview.vector v
            INNER JOIN interview.meta_df m ON v.doc_id = m.doc_id
        """
        
        # 필터 조건 추가
        where_clauses = []
        if filter:
            if "occupation" in filter:
                where_clauses.append("m.occupation = %s")
                params.append(filter["occupation"])
            if "question_intent" in filter:
                where_clauses.append("m.question_intent = %s")
                params.append(filter["question_intent"])
        
        if where_clauses:
            sql_query += " WHERE " + " AND ".join(where_clauses)
        
        sql_query += """
            ORDER BY v.embedding <-> %s::vector
            LIMIT %s
        """
        params.extend([query_emb, k])
        
        with self.conn.cursor() as cur:
            cur.execute(sql_query, tuple(params))
            rows = cur.fetchall()
        
        return self._hydrate_documents(rows)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Document, float]]:
        """면접 데이터 유사도 검색 (점수 포함)"""
        query_emb = self.embedding_fn.embed_query(query)
        
        sql_query = """
            SELECT 
                m.doc_id,
                m.occupation,
                m.gender,
                m.age_range,
                m.experience,
                m.question_intent,
                m.answer_intent_category,
                m.answer_emotion_category,
                m.question_text,
                m.answer_text,
                m.content_combined,
                v.chunk_id,
                v.chunk_seq,
                (v.embedding <-> %s::vector) AS distance
            FROM interview.vector v
            INNER JOIN interview.meta_df m ON v.doc_id = m.doc_id
        """
        params: List[Any] = [query_emb]
        where_clauses = []
        if filter:
            if "occupation" in filter:
                where_clauses.append("m.occupation = %s")
                params.append(filter["occupation"])
            if "question_intent" in filter:
                where_clauses.append("m.question_intent = %s")
                params.append(filter["question_intent"])
        if where_clauses:
            sql_query += " WHERE " + " AND ".join(where_clauses)
        
        sql_query += """
            ORDER BY distance
            LIMIT %s
        """
        params.append(k)
        
        with self.conn.cursor() as cur:
            cur.execute(sql_query, tuple(params))
            rows = cur.fetchall()
        
        documents = []
        for row in rows:
            *doc_fields, distance = row
            doc = self._hydrate_row(tuple(doc_fields))
            documents.append((doc, float(distance)))
        
        return documents
    
    def _hydrate_documents(self, rows: List[Tuple[Any, ...]]) -> List[Document]:
        """데이터베이스 행을 Document 객체로 변환"""
        documents: List[Document] = []
        for row in rows:
            doc = self._hydrate_row(row)
            documents.append(doc)
        return documents
    
    def _hydrate_row(self, row: Tuple[Any, ...]) -> Document:
        """단일 행을 Document 객체로 변환"""
        (
            doc_id,
            occupation,
            gender,
            age_range,
            experience,
            question_intent,
            answer_intent_category,
            answer_emotion_category,
            question_text,
            answer_text,
            content_combined,
            chunk_id,
            chunk_seq,
        ) = row
        
        # 메타데이터 구성
        metadata: Dict[str, Any] = {
            "doc_id": doc_id,
            "occupation": occupation,
            "gender": gender,
            "age_range": age_range,
            "experience": experience,
            "question_intent": question_intent,
            "answer_intent_category": answer_intent_category,
            "answer_emotion_category": answer_emotion_category,
            "chunk_id": chunk_id,
            "chunk_seq": chunk_seq,
        }
        
        # content는 질문+답변 조합
        page_content = f"[질문] {question_text}\n\n[답변] {answer_text}"
        
        return Document(page_content=page_content, metadata=metadata)

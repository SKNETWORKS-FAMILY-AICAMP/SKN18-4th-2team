from typing import Any, Dict, List, Optional, Tuple
import psycopg2
from difflib import SequenceMatcher

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
        """면접 데이터 유사도 검색 (메타데이터 필터링 지원, doc_id 중복 제거)
        
        필터링된 결과가 부족하면 자동으로 필터를 완화합니다:
        1. occupation + question_intent 둘 다 필터링
        2. 결과 부족시 → occupation만 필터링 (같은 직군 내 다른 유형)
        3. 여전히 부족시 → question_intent만 필터링 (다른 직군 + 같은 유형)
        4. 최후 수단 → 필터 없이 검색
        """
        query_emb = self.embedding_fn.embed_query(query)
        
        # Fallback 전략: 필터 우선순위
        # 사용자가 지정한 occupation을 최대한 유지하면서 intent를 확장
        filter_strategies = []
        if filter:
            # 전략 1: 모든 필터 적용 (occupation + question_intent)
            if "occupation" in filter and "question_intent" in filter:
                filter_strategies.append(filter.copy())
                # 전략 2: 같은 occupation + intent 제거 (같은 직군 내 다른 유형)
                filter_strategies.append({"occupation": filter["occupation"]})
                # 전략 3: question_intent만 (다른 직군 + 같은 유형)
                filter_strategies.append({"question_intent": filter["question_intent"]})
            elif "question_intent" in filter:
                # question_intent만 있으면 그것만 먼저
                filter_strategies.append(filter.copy())
            elif "occupation" in filter:
                # occupation만 있으면 그것만
                filter_strategies.append(filter.copy())
            # 전략 4: 필터 없이 (최후 수단)
            filter_strategies.append({})
        else:
            filter_strategies.append({})
        
        # 각 전략별로 시도 (기존 결과를 유지하면서 추가)
        seen_doc_ids = set()
        seen_questions = []  # 이미 추가된 질문 텍스트
        unique_rows = []
        
        for strategy_filter in filter_strategies:
            # 부족한 개수만큼만 추가로 검색
            needed = k - len(unique_rows)
            if needed <= 0:
                break
                
            new_rows = self._search_with_filter(query_emb, needed, strategy_filter, exclude_doc_ids=seen_doc_ids)
            # print(f"[DEBUG] Strategy {strategy_filter}: Found {len(new_rows)} rows")
            
            for row in new_rows:
                doc_id = row[0]
                question_text = row[8]  # question_text는 9번째 컨럼
                
                # doc_id 중복 체크
                if doc_id in seen_doc_ids:
                    # print(f"[DEBUG] Skipping doc_id {doc_id} - already seen")
                    continue
                
                # 질문 텍스트 유사도 체크 (0.55 이상이면 중복으로 간주)
                is_duplicate = False
                for seen_q in seen_questions:
                    similarity = SequenceMatcher(None, question_text, seen_q).ratio()
                    if similarity > 0.55:  # 의미적 중복 포착 (0.57 정도면 거의 같은 질문)
                        # print(f"[DEBUG] Duplicate found! Similarity {similarity:.2f}")
                        # print(f"[DEBUG]   Current: {question_text[:50]}...")
                        # print(f"[DEBUG]   Seen: {seen_q[:50]}...")
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    print(f"[DEBUG] Adding question: {question_text[:50]}...")
                    seen_doc_ids.add(doc_id)
                    seen_questions.append(question_text)
                    unique_rows.append(row)
                    if len(unique_rows) >= k:
                        break
        
        # Document 변환
        documents = []
        for row in unique_rows:
            *doc_fields, distance = row
            doc = self._hydrate_row(tuple(doc_fields))
            documents.append(doc)
        return documents
    
    def _search_with_filter(
        self,
        query_emb: List[float],
        k: int,
        filter: Dict[str, Any],
        exclude_doc_ids: set = None
    ) -> List[Tuple[Any, ...]]:
        """특정 필터로 검색 실행 (내부 헬퍼 함수)
        
        Args:
            exclude_doc_ids: 제외할 doc_id 집합 (이미 검색된 결과)
        """
        params: List[Any] = []
        if exclude_doc_ids is None:
            exclude_doc_ids = set()
        
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
        
        # 필터 조건 추가
        where_clauses = []
        
        # 제외할 doc_id 추가
        if exclude_doc_ids:
            placeholders = ",".join(["%s"] * len(exclude_doc_ids))
            where_clauses.append(f"m.doc_id NOT IN ({placeholders})")
            params.extend(list(exclude_doc_ids))
        
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
        params.insert(0, query_emb)
        params.append(k * 5)  # 중복 제거를 고려하여 5배 가져오기 (유사 질문 많음)
        
        with self.conn.cursor() as cur:
            cur.execute(sql_query, tuple(params))
            rows = cur.fetchall()
        
        # doc_id 중복 제거 제거 (외부에서 처리)
        return rows
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Document, float]]:
        """면접 데이터 유사도 검색 (점수 포함, 필터링 지원, doc_id 중복 제거)
        
        필터링된 결과가 부족하면 자동으로 필터를 완화합니다:
        1. occupation + question_intent 둘 다 필터링
        2. 결과 부족시 → occupation만 필터링 (같은 직군 내 다른 유형)
        3. 여전히 부족시 → question_intent만 필터링 (다른 직군 + 같은 유형)
        4. 최후 수단 → 필터 없이 검색
        """
        query_emb = self.embedding_fn.embed_query(query)
        
        # Fallback 전략: 필터 우선순위
        # 사용자가 지정한 occupation을 최대한 유지하면서 intent를 확장
        filter_strategies = []
        if filter:
            # 전략 1: 모든 필터 적용 (occupation + question_intent)
            if "occupation" in filter and "question_intent" in filter:
                filter_strategies.append(filter.copy())
                # 전략 2: 같은 occupation + intent 제거 (같은 직군 내 다른 유형)
                filter_strategies.append({"occupation": filter["occupation"]})
                # 전략 3: question_intent만 (다른 직군 + 같은 유형)
                filter_strategies.append({"question_intent": filter["question_intent"]})
            elif "question_intent" in filter:
                # question_intent만 있으면 그것만 먼저
                filter_strategies.append(filter.copy())
            elif "occupation" in filter:
                # occupation만 있으면 그것만
                filter_strategies.append(filter.copy())
            # 전략 4: 필터 없이 (최후 수단)
            filter_strategies.append({})
        else:
            filter_strategies.append({})
        
        # 각 전략별로 시도 (기존 결과를 유지하면서 추가)
        seen_doc_ids = set()
        seen_questions = []  # 이미 추가된 질문 텍스트
        unique_rows = []
        
        for strategy_filter in filter_strategies:
            # 부족한 개수만큼만 추가로 검색
            needed = k - len(unique_rows)
            if needed <= 0:
                break
                
            new_rows = self._search_with_filter(query_emb, needed, strategy_filter, exclude_doc_ids=seen_doc_ids)
            # print(f"[DEBUG-SCORE] Strategy {strategy_filter}: Found {len(new_rows)} rows")
            
            for row in new_rows:
                doc_id = row[0]
                question_text = row[8]  # question_text는 9번째 컨럼
                
                # doc_id 중복 체크
                if doc_id in seen_doc_ids:
                    # print(f"[DEBUG-SCORE] Skipping doc_id {doc_id} - already seen")
                    continue
                
                # 질문 텍스트 유사도 체크 (0.55 이상이면 중복으로 간주)
                is_duplicate = False
                for seen_q in seen_questions:
                    similarity = SequenceMatcher(None, question_text, seen_q).ratio()
                    if similarity > 0.55:  # 의미적 중복 포착 (0.57 정도면 거의 같은 질문)
                        # print(f"[DEBUG-SCORE] Duplicate found! Similarity {similarity:.2f}")
                        # print(f"[DEBUG-SCORE]   Current: {question_text[:50]}...")
                        # print(f"[DEBUG-SCORE]   Seen: {seen_q[:50]}...")
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    # print(f"[DEBUG-SCORE] Adding question: {question_text[:50]}...")
                    seen_doc_ids.add(doc_id)
                    seen_questions.append(question_text)
                    unique_rows.append(row)
                    if len(unique_rows) >= k:
                        break
        
        # Document 변환 (점수 포함)
        documents = []
        for row in unique_rows:
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
from typing import Any, Dict, List, TypedDict

class Chunk(TypedDict):
    content: str
    score: float
    metadata: Dict[str, Any]


class GraphState(TypedDict):
    user: str # form 기반 input
    question: str # 사용자 input

    generate_question: str # 질문 재생성

    category: str # classify 이후 카테고리(면접/대학진로)
    category_rag_finetune: str

    chunks: List[Chunk]
    final_chunks: List[Chunk]

    answer: str
    final_answer: str
    
    # 면접 관련 필드
    interview_query_type: str  # "question_recommendation" 또는 "answer_feedback"
    interview_keywords: List[str]  # 추출된 키워드 (질문 추천일 경우)
    classification_reason: str  # 질문 유형 분류 이유
    
    # 면접 chunk 평가 필드
    eval_score: float  # chunk 평가 점수
    eval_reason: str  # chunk 평가 이유


    
    

    


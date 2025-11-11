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

    chunks: List[Chunk]
    final_chunks: List[Chunk]

    answer: str
    final_answer: str


    
    

    


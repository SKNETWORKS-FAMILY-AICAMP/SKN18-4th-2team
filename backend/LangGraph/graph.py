from langgraph.graph import StateGraph, END

from .initstate import GraphState
from .nodes.classify import classify_category
from .nodes.retrieve_chunks import retrieve_chunks_node
from .nodes.eval_chunks import node_evaluate_chunks
from .nodes.generate_questions import generate_user_question_node
from .nodes.generate_answer import generate_answer
from .nodes.eval_generated_answer import evaluate_question_answer

def create_graph_flow():
    """
    ✅ LangGraph 전체 파이프라인 빌더
    classify → retrieve → eval_chunks → generate_question → generate_answer(ft_model) → evaluate_answer
    """
    graph = StateGraph(GraphState)

    # 1️⃣ 노드 등록
    graph.add_node('classify', classify_category)
    graph.add_node('retrieve', retrieve_chunks_node)
    graph.add_node('evaluate_chunks', node_evaluate_chunks)
    graph.add_node('remake_question', generate_user_question_node)
    graph.add_node('generate_answer', generate_answer)
    graph.add_node('evaluate_answer', evaluate_question_answer)
    

    # 2️⃣ 엣지 연결 (흐름 정의)
    graph.set_entry_point("classify")

    graph.add_edge("classify", "retrieve")              # 질문 분류 후 → chunk 검색
    graph.add_edge("retrieve", "evaluate_chunks")       # 검색된 chunk → 관련도 평가
    graph.add_edge("evaluate_chunks", "generate_question")  # 상위 청크 기반 질문 리메이크
    graph.add_edge("generate_question", "generate_answer")  # 리메이크된 질문으로 답변 생성
    graph.add_edge("generate_answer", "evaluate_answer")    # 생성된 답변 평가
    graph.add_edge("evaluate_answer", END)                 # 그래프 종료

    # 3️⃣ 컴파일 및 리턴
    app = graph.compile()
    print("✅ LangGraph 파이프라인 컴파일 완료")
    return app
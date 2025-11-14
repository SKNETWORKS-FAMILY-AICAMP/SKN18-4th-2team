from langgraph.graph import StateGraph, END

from .initstate import GraphState
from .nodes.classify import classify_category, route_after_classify
from .nodes.classify_rag_finetune import classify_rag_finetune, route_rag_finetune
from .nodes.retrieve_chunks import retrieve_chunks_node
from .nodes.eval_chunks import node_evaluate_chunks
from .nodes.generate_questions import generate_user_question_node
from .nodes.generate_answer import generate_answer
from .nodes.eval_generated_answer import evaluate_question_answer

# 면접 관련 노드 import
from .nodes.interview_query_classify import interview_query_classify_node
from .nodes.interview_vector_search import interview_vector_search_node, route_after_interview_vector_search
from .nodes.interview_eval import interview_eval_node
from .nodes.interview_generation import interview_generation_node

def create_graph_flow():
    graph = StateGraph(GraphState)

    # 기존 대학진로 관련 노드
    graph.add_node('classify', classify_category)
    graph.add_node('classify_rag_finetune', classify_rag_finetune)
    graph.add_node('retrieve', retrieve_chunks_node)
    graph.add_node('evaluate_chunks', node_evaluate_chunks)
    graph.add_node('generate_answer', generate_answer)
    graph.add_node('evaluate_answer', evaluate_question_answer)
    
    # 면접 관련 노드 추가
    graph.add_node('interview_query_classify', interview_query_classify_node)
    graph.add_node('remake_question', generate_user_question_node)
    graph.add_node('interview_vector_search', interview_vector_search_node)
    graph.add_node('interview_eval', interview_eval_node)
    graph.add_node('interview_generation', interview_generation_node)

    # # 시작점
    graph.set_entry_point('classify')

    graph.add_conditional_edges(
        'classify',
        route_after_classify,
        {
            "interview": "interview_query_classify",
            "college": "classify_rag_finetune",
            "etc": END,
        },
    )

    graph.add_edge('interview_query_classify', 'interview_vector_search')
    graph.add_conditional_edges(
        'interview_vector_search',
        route_after_interview_vector_search,
        {
            "remake": "remake_question",
            "eval_chunk": "interview_eval",
        },
    )
    graph.add_edge('remake_question', 'interview_vector_search')    # 재작성 질문으로 재검색
    graph.add_edge('interview_eval', 'interview_generation')
    graph.add_edge('interview_generation', END)
    return graph.compile()

    # --- 대학·RAG 플로우 ---
    graph.add_edge('retrieve', 'evaluate_chunks')
    graph.add_conditional_edges(
        'evaluate_chunks',
        route_after_chunk_eval,              # 점수 기반으로 분기
        {
            "answer": 'generate_answer',
            "retry": 'remake_question',      # 질문 재작성 후 다시 retrieve로 가게끔
            "fail": END,
        },
    )
    graph.add_edge('remake_question', 'retrieve')
    graph.add_edge('generate_answer', 'evaluate_answer')
    graph.add_edge('evaluate_answer', END)
    return graph.compile()

    ###############################################
    #  GraphState에 재작성 점수 State 추가
    # question_rewrite_attempts: int
    # chunk_eval_top_score: float
    # interview_question_rewrites: int
    # interview_chunk_top_score: float

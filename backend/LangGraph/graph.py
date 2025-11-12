from langgraph.graph import StateGraph, END

from initstate import GraphState
from nodes.classify import classify_category
from nodes.retrieve_chunks import retrieve_chunks_node
from nodes.eval_chunks import node_evaluate_chunks
from nodes.generate_questions import generate_user_question_node
from nodes.generate_answer import generate_answer
from nodes.eval_generated_answer import evaluate_question_answer

# 면접 관련 노드 import
from nodes.interview_query_classify import interview_query_classify_node
from nodes.interview_vector_search import interview_vector_search_node
from nodes.interview_eval import interview_eval_node
from nodes.interview_generation import interview_generation_node

def create_graph_flow():
    graph = StateGraph(GraphState)

    # 기존 대학진로 관련 노드
    graph.add_node('classify', classify_category)
    graph.add_node('retrieve', retrieve_chunks_node)
    graph.add_node('evaluate_chunks', node_evaluate_chunks)
    graph.add_node('remake_question', generate_user_question_node)
    graph.add_node('generate_answer', generate_answer)
    graph.add_node('evaluate_answer', evaluate_question_answer)
    
    # 면접 관련 노드 추가
    graph.add_node('interview_query_classify', interview_query_classify_node)
    graph.add_node('interview_vector_search', interview_vector_search_node)
    graph.add_node('interview_eval', interview_eval_node)
    graph.add_node('interview_generation', interview_generation_node)

    # 엣지 연결
    # 시작점
    graph.set_entry_point('classify')
    
    # classify 이후 분기: 면접 vs 대학진로
    def route_after_classify(state: GraphState) -> str:
        category = state.get("category", "").strip()
        if "면접" in category:
            return "interview_query_classify"
        else:
            return "retrieve"
    
    graph.add_conditional_edges(
        'classify',
        route_after_classify,
        {
            "interview_query_classify": "interview_query_classify",
            "retrieve": "retrieve"
        }
    )
    
    # 면접 플로우: classify -> interview_query_classify -> interview_vector_search -> interview_eval -> interview_generation -> END
    graph.add_edge('interview_query_classify', 'interview_vector_search')
    graph.add_edge('interview_vector_search', 'interview_eval')
    graph.add_edge('interview_eval', 'interview_generation')
    graph.add_edge('interview_generation', END)
    
    # 대학진로 플로우: classify -> retrieve -> evaluate_chunks -> remake_question -> generate_answer -> evaluate_answer -> END
    graph.add_edge('retrieve', 'evaluate_chunks')
    graph.add_edge('evaluate_chunks', 'remake_question')
    graph.add_edge('remake_question', 'generate_answer')
    graph.add_edge('generate_answer', 'evaluate_answer')
    graph.add_edge('evaluate_answer', END)
    
    return graph.compile()

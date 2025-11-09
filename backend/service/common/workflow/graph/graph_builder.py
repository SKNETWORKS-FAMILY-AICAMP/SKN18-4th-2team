from langgraph.graph import StateGraph, END

from workflow.states.graph_state import GraphState
# from workflow.nodes.classify_node import classify_node
# from workflow.nodes.question_node import question_node
# from workflow.nodes.interview_retrieve_node import interview_retrieve_node
# from workflow.nodes.interview_eval_node import interview_eval_node
# from workflow.nodes.interview_generate_node import interview_generate_node
# from workflow.nodes.college_retrieve_node import college_retrieve_node
# from workflow.nodes.college_eval_node import college_eval_node
# from workflow.nodes.college_generate_node import college_generate_node
# from workflow.nodes.fallback_node import fallback_node


def _route_evaluate_interview(state: GraphState) -> str:
    if state.eval_score and state.eval_score >= 0.7:
        return "interview_generate"
    if state.retry_count >= 1:
        return "fallback"
    return "interview_retrieve"


def _route_evaluate_college(state: GraphState) -> str:
    if state.eval_score and state.eval_score >= 0.7:
        return "college_generate"
    if state.retry_count >= 1:
        return "fallback"
    if state.request_more_web:
        return "college_retrieve"
    return "tavily_retry"


def create_graph_flow() -> StateGraph:
    graph = StateGraph(GraphState)

    graph.add_node("classify", classify_node)
    graph.add_node("question", question_node)
    graph.add_node("interview_retrieve", interview_retrieve_node)
    graph.add_node("interview_eval", interview_eval_node)
    graph.add_node("interview_generate", interview_generate_node)
    graph.add_node("college_retrieve", college_retrieve_node)   # 내부에서 RDB/VDB/Tavily fan-out
    graph.add_node("college_eval", college_eval_node)
    graph.add_node("college_generate", college_generate_node)
    graph.add_node("fallback", fallback_node)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "question")

    # 면접 플로우
    graph.add_edge("question", "interview_retrieve", condition=lambda s: s.scenario == "interview")
    graph.add_edge("interview_retrieve", "interview_eval")
    graph.add_conditional_edges("interview_eval", _route_evaluate_interview, {
        "interview_generate": "interview_generate",
        "interview_retrieve": "interview_retrieve",
        "fallback": "fallback",
    })
    graph.add_edge("interview_generate", END)

    # 대학 플로우
    graph.add_edge("question", "college_retrieve", condition=lambda s: s.scenario == "college")
    graph.add_edge("college_retrieve", "college_eval")
    graph.add_conditional_edges("college_eval", _route_evaluate_college, {
        "college_generate": "college_generate",
        "college_retrieve": "college_retrieve",
        "tavily_retry": "college_retrieve",  # 재검색도 같은 노드 재사용
        "fallback": "fallback",
    })
    graph.add_edge("college_generate", END)

    graph.add_edge("fallback", END)

    return graph

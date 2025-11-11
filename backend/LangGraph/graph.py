from langgraph.graph import StateGraph, END

from initstate import GraphState
from nodes.classify import classify_category
from nodes.retrieve_chunks import retrieve_chunks_node
from nodes.eval_chunks import node_evaluate_chunks
from nodes.generate_questions import generate_user_question_node
from nodes.generate_answer import generate_answer
from nodes.eval_generated_answer import evaluate_question_answer

def create_graph_flow():
    graph = StateGraph(GraphState)

    graph.add_node('classify', classify_category)
    graph.add_node('retrieve', retrieve_chunks_node)
    graph.add_node('evaluate_chunks', node_evaluate_chunks)
    graph.add_node('remake_question', generate_user_question_node)
    graph.add_node('generate_answer', generate_answer)
    graph.add_node('evaluate_answer', evaluate_question_answer)
    

    # TODOS: 엣지 연결

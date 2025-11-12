from langchain_core.messages import HumanMessage, SystemMessage

from models import load_ollama_model

from initstate import GraphState

def generate_user_question_node(state: GraphState) -> GraphState:
    """질문 재생성 노드"""
    llm = load_ollama_model()
    quetion = state['question']
    message = [
        SystemMessage(
            content=(

            )
        ),
        HumanMessage(
            content=(

            )
        )
    ]
    data = llm.invoke(message).content
    # 예외처리필요
    state['generate_question'] = data

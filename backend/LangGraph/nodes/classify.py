from models import load_ollama_model
from initstate import GraphState

from langchain_core.messages import HumanMessage, SystemMessage

def classify_category(state: GraphState) -> GraphState:
    """카테고리 분류 노드""" 
    llm = load_ollama_model()
    message = [
        SystemMessage(
            content=(
                "너는 사용자 요청을 '면접' 또는 '대학진로' 중 하나로만 분류하는 시스템입니다. "
                "다음 정보를 참고하여 최종 카테고리를 결정하세요.\n"
                f"- 사용자 정보(배경/목표 등): {state['user']}\n"
                f"- 사용자 질문: {state['question']}\n\n"
                "판단 기준:\n"
                "1. 면접 준비, 인성/직무 면접 질문, 회사 지원 동기 등 채용 또는 취업 인터뷰에 관한 요구라면 '면접'으로 분류합니다.\n"
                "2. 학과 선택, 대학 정보, 진학 전략, 전공/교과 관련 고민 등 진학이나 전공 탐색과 직접적으로 연결되면 '대학진로'로 분류합니다.\n"
                "3. 사용자의 상황(state['user'])가 취업 준비생이라면 면접 쪽을 우선 고려하고, 고등학생이라면 대학진로를 우선 고려합니다.\n"
                "4. 애매한 경우 질문에서 더 직접적으로 다루는 주제를 선택합니다.\n\n"
                "출력 형식: 오직 '면접' 또는 '대학진로' 중 하나만 반환하세요."
            )
        ),

        HumanMessage(
            content=f"질문: 유저의 현재 상태를 고려해서 {state['question']}에 해당하는 카테고리를 분류하세요."
        ),
    ]
    raw = llm.invoke(message).content
    state["category"] = raw
    return state

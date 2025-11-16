from models import load_ollama_model
from initstate import GraphState

from langchain_core.messages import HumanMessage, SystemMessage

def classify_rag_finetune(state: GraphState) -> GraphState:
    """카테고리 분류 노드""" 
    llm = load_ollama_model()
    message = [
        SystemMessage(
            content=(
                "너는 사용자의 질문을 보고 RAG 파이프라인으로 답해야 할지, "
                "파인튜닝된 상담형 모델로 답해야 할지 결정하는 분류기다.\n"
                "RAG VectorDB에는 학과 요약, 관련 흥미/적성, 학과 특성 같은 "
                "사실 기반 정보가 임베딩되어 있다. 특정 학과, 전공 비교, 진로 정보, "
                "커리큘럼, 적성 매칭처럼 구체적인 학과 지식이 필요한 질문이면 반드시 'rag'를 선택하라.\n"
                "Finetuning 모델은 \"나 공부를 못하는데 어떻게 하는 게 좋을까?\"처럼 "
                "동기 부여, 학습 태도, 멘탈 케어, 공부 방법 조언 등 개인 고민을 다루는 데이터로 학습되었다. "
                "감정 공감이나 추상적인 고민 상담이 필요한 질문이면 'finetune'을 선택하라.\n"
                "판단 기준:\n"
                "1. 학과 정보/비교/추천/적성 진단 → 'rag'\n"
                "2. 성적 걱정, 공부 법, 멘탈 관리, 동기 부여 등 개인 고민 → 'finetune'\n"
                "3. 애매하면, 구체적 사실 확인이 필요하면 'rag', 주관적 조언이면 'finetune'\n"
                "출력 형식: 소문자로 'rag' 또는 'finetune' 중 하나만 반환하라."
            )
        ),

        HumanMessage(
            content=f"질문: 유저의 질문을 분석하여 {state['question']}에 해당하는 카테고리를 분류하세요."
        ),
    ]
    raw = llm.invoke(message).content
    state["category_rag_finetune"] = raw
    return state

def route_rag_finetune(state: GraphState) -> str:
    category = state.get("category_rag_finetune", "").strip()
    return category

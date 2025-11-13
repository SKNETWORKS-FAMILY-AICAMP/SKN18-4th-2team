from langchain_core.messages import HumanMessage, SystemMessage

from models import load_ollama_model

from initstate import GraphState


def generate_user_question_node(state: GraphState) -> GraphState:
    """사용자 질문을 RAG 검색에 적합한 형태로 재작성"""
    llm = load_ollama_model()
    raw_question = (state.get("question") or "").strip()  # 사용자의 질문
    user_profile = (state.get("user") or "").strip()  # 사용자의 프로필
    category = (state.get("category") or "일반").strip()  # 사용자의 카테고리

    # 질문이 없다면
    if not raw_question:
        state["generate_question"] = ""
        return state

    # 프롬프트 설정
    system_prompt = (
        "너는 진로/취업 상담 챗봇의 질문 정제기다. "
        "사용자의 배경과 의도를 살려 핵심을 명확하게 드러내는 질문을 한 문단으로 재작성하라. "
        "불필요한 감탄사나 모호한 표현을 제거하고, 구체적 상황과 기대하는 답변 범위를 함께 담아라."
    )

    human_prompt = (
        f"사용자 배경:\n{user_profile or '제공되지 않음'}\n\n"
        f"카테고리: {category}\n\n"
        f"원본 질문:\n{raw_question}\n\n"
        "위 정보를 기반으로 사용자의 의도를 해치지 않도록 질문 하나를 재생성하라."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        refined_question = llm.invoke(messages).content.strip()
    except Exception:
        refined_question = ""

    state["generate_question"] = refined_question or raw_question
    return state

from langchain_core.messages import HumanMessage, SystemMessage

from models import load_ollama_model

from initstate import GraphState


def generate_user_question_node(state: GraphState) -> GraphState:
    """사용자 질문을 RAG 검색에 적합한 단일 쿼리로 정제한다."""
    llm = load_ollama_model()
    raw_question = (state.get("question") or "").strip()
    user_profile = (state.get("user") or "").strip()
    category = (state.get("category") or "일반").strip()

    if not raw_question:
        state["generate_question"] = ""
        return state

    system_prompt = (
        "너는 진로/취업 상담 챗봇의 질문 정제기다. "
        "사용자의 배경과 의도를 살려 핵심이 명확한 검색 친화적 질문을 1개 작성하라. "
        "불필요한 감탄사나 모호한 표현을 제거하고, 필요한 조건과 목표를 한 문단 안에 포함하라."
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

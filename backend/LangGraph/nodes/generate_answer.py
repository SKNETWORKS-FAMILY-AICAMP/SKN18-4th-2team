from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from models import load_ollama_model
from initstate import GraphState


def _chunks_to_context(chunks: List[Dict[str, Any]], limit: int = 5) -> str:
    """선택된 chunk 들을 사람이 읽기 쉬운 문맥 문자열로 변환한다."""
    if not chunks:
        return ""

    formatted = []
    for idx, chunk in enumerate(chunks[:limit], start=1):
        metadata = chunk.get("metadata") or {}
        source = ", ".join(f"{k}: {v}" for k, v in metadata.items() if v)
        snippet = chunk.get("content", "").strip()
        formatted.append(f"[자료 {idx}] {source}\n{snippet}".strip())
    return "\n\n".join(formatted)


def generate_answer(state: GraphState) -> GraphState:
    """평가된 chunk를 활용해 구조화된 답변을 생성한다."""
    llm = load_ollama_model()

    base_question = (state.get("generate_question") or state.get("question") or "").strip()
    user_profile = (state.get("user") or "").strip()
    category = (state.get("category") or "일반").strip()
    context_chunks = state.get("final_chunks") or state.get("chunks") or []
    context_text = _chunks_to_context(context_chunks)

    system_prompt = (
        "너는 진로/취업 컨설턴트다. 제공된 참고 문서를 우선 근거로 활용해 "
        "사용자 질문에 대해 실행 가능한 조언을 한국어로 작성하라. "
        "답변은 1) 상황 요약 2) 실행 전략(불릿) 3) 참고/주의 사항 순으로 구성한다. "
        "참고 문서가 없다면 그 사실을 먼저 알리고 일반적인 모범 답안을 제시하라."
    )

    human_prompt = (
        f"사용자 배경:\n{user_profile or '제공되지 않음'}\n\n"
        f"카테고리: {category}\n"
        f"질문:\n{base_question or '질문 정보 없음'}\n\n"
        f"참고 자료:\n{context_text or '없음'}\n\n"
        "상기 정보를 활용해 신뢰할 수 있는 한국어 답변을 작성하라."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        answer_text = llm.invoke(messages).content.strip()
    except Exception:
        answer_text = ""

    state["answer"] = answer_text or "답변을 생성하지 못했습니다. 다시 시도해 주세요."
    return state

from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from models import load_finetune_ollama_model, load_openai_model
from initstate import GraphState

import os


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


def _extract_university_list(chunks: List[Dict[str, Any]]) -> List[str]:
    """청크 메타데이터에 포함된 대학/학과 목록만 추출한다."""
    if not chunks:
        return []

    seen = set()
    universities: List[str] = []
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        uni_field = metadata.get("universities") or metadata.get("Universities") or ""
        if not uni_field:
            continue
        entries = [entry.strip() for entry in uni_field.split("|")]
        for entry in entries:
            if entry and entry not in seen:
                seen.add(entry)
                universities.append(entry)
    return universities


def generate_answer(state: GraphState) -> GraphState:
    """평가된 chunk를 활용해 구조화된 답변을 생성한다."""
    base_question = (state.get("generate_question") or state.get("question") or "").strip()
    user_profile = (state.get("user") or "").strip()
    category = (state.get("category") or "일반").strip()
    context_chunks = state.get("final_chunks") or state.get("chunks") or []
    context_text = _chunks_to_context(context_chunks)
    allowed_universities = _extract_university_list(context_chunks)
    universities_text = (
        "\n".join(f"- {name}" for name in allowed_universities)
        if allowed_universities
        else "없음 (대학명을 새로 만들지 말고 언급도 피하라)"
    )

    has_context = bool(context_text.strip())
    params = {"model": os.getenv("EVAL_MODEL")}
    llm = load_openai_model(params_key=tuple(sorted(params.items()))) if has_context else load_finetune_ollama_model()

    if has_context:
        system_prompt = (
            "너는 진로/취업 컨설턴트다. 제공된 참고 문서를 우선 근거로 활용해 "
            "사용자 질문에 대해 실행 가능한 조언을 한국어로 작성하라. 답변은 아래 구조를 따른다.\n"
            "1) 학과 설명: 각 참고 자료의 summary, interest, property 필드를 근거로 학과의 특징/적성/진로를 정리한다.\n"
            "2) 실행 전략(불릿)\n"
            "3) 학과 추천: 참고 자료의 universities 메타데이터에서 추출한 대학명만 사용하되, 주어진 목록을 빠짐없이 나열한다.\n"
            "4) 참고/주의 사항\n"
            "각 섹션은 '학과 설명:', '실행 전략 1)'처럼 제목을 명시한 단락으로 작성하고, 실행 전략과 학과 추천 항목은 각각 '실행 전략 1)', '학과 추천 1)'과 같은 번호 매김 문장으로 나열하라.\n"
            "각 실행 전략 블록에서는 구체적인 학과/전공명을 언급하고, 해당 참고 자료의 메타데이터에 "
            "'universities' 정보가 포함되어 있다면 최소 1개 이상의 대학명을 자연스럽게 인용하라. "
            "제공된 참고 문서는 DB에서 검색된 내용이므로, 새로운 자료를 상상하거나 외부 지식을 추가하지 말고 "
            "반드시 주어진 문맥 안에서만 사실을 언급하라. "
            "대학/학과 명칭은 반드시 아래 허용 목록에 포함된 항목만 사용하고, 목록에 없는 이름을 새로 만들지 마라. "
            "출력은 순수 텍스트로만 작성하며, 섹션 사이에는 빈 줄 하나를 넣고, **, *, -, • 같은 마크다운/특수 기호를 사용하지 마라. "
            "해당 섹션에 넣을 내용이 없다면 그 섹션 자체를 생략하되, 빈 텍스트나 placeholder를 넣지 마라."
        )
        human_prompt = (
            f"[사용자 배경]\n{user_profile or '제공되지 않음'}\n\n"
            f"[질문]\n{base_question or '질문 정보 없음'}\n\n"
            f"[참고 자료]\n{context_text}\n\n"
            f"[사용 가능 대학 목록]\n{universities_text}\n\n"
            "위 정보를 근거로 지정된 답변 구조(학과 설명 → 실행 전략 → 학과 추천 → 참고/주의 사항)를 따른다. "
            "학과 설명에는 summary/interest/property만 사용하고, 학과 추천에는 허용 목록에 있는 대학명 전부를 빠짐없이 활용한다. "
            "사용할 수 있는 참고 자료 번호가 없다면 다른 섹션으로 넘어가고, 임의의 번호를 만들지 마라."
        )
    else:
        system_prompt = (
            "너는 진로/취업 상담 전문가다. 참고 문서 없이도 사용자의 질문에 대해 "
            "공감과 실행 가능한 조언을 한국어로 제공해야 한다. "
            "답변은 1) 상황 요약 2) 실행 전략(불릿) 3) 참고/주의 사항 순으로 구성하고, "
            "각 섹션은 '상황 요약:', '실행 전략 1)'과 같이 제목/번호를 붙인 문장으로 작성하라. "
            "잡음이나 반복 없이 명료한 문장으로 작성하고, 섹션 사이에는 빈 줄을 넣어 구분하라. "
            "출력은 순수 텍스트로 작성하고 마크다운(**, *, -, • 등) 표기를 쓰지 마라."
        )
        human_prompt = (
            f"사용자 배경:\n{user_profile or '제공되지 않음'}\n\n"
            f"카테고리: {category}\n"
            f"질문:\n{base_question or '질문 정보 없음'}\n\n"
            "참고 자료는 제공되지 않았다. "
            "상담 관점에서 현실적인 조언과 격려를 포함한 답변을 작성하라."
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

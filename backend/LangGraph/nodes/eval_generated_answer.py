import json
import os
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from models import load_openai_model
from initstate import GraphState


def _summarize_chunks(chunks: List[Dict[str, Any]], limit: int = 3) -> str:
    """선택된 chunk 들을 간결한 텍스트 블록으로 요약한다."""
    if not chunks:
        return ""

    lines = []
    for idx, chunk in enumerate(chunks[:limit], start=1):
        metadata = chunk.get("metadata") or {}
        meta_str = ", ".join(f"{key}: {value}" for key, value in metadata.items() if value)
        snippet = chunk.get("content", "").strip()
        lines.append(f"[출처 {idx}] {meta_str}\n{snippet}".strip())
    return "\n\n".join(lines)


def evaluate_question_answer(state: GraphState) -> GraphState:
    """생성된 답변을 검증하고 필요 시 교정된 답변과 평가 리포트를 저장한다."""
    question = (state.get("question") or "").strip()
    draft_answer = (state.get("answer") or "").strip()
    supporting_chunks = state.get("final_chunks") or state.get("chunks") or []

    if not draft_answer:
        state["final_answer"] = ""
        state["answer_eval"] = {
            "score": 0.0,
            "verdict": "retry",
            "issues": ["초안 답변이 존재하지 않습니다."],
        }
        return state

    params = {"model": os.getenv("EVAL_MODEL")}
    llm = load_openai_model(params_key=tuple(sorted(params.items())))

    context_snippets = _summarize_chunks(supporting_chunks)
    system_prompt = (
        "너는 RAG 시스템의 엄격한 검수관이다. 사용자 질문, 초안 답변, 참고 문맥을 보고 "
        "답변이 질문을 해결하는지, 사실 오류가 없는지, 참고 문맥을 벗어나지 않는지 확인하라. "
        "필요 시 답변을 간결히 고치되 새로운 사실을 발명하지 말고 주어진 문맥 내 정보만 사용하라. "
        "JSON 문자열 하나만 반환하며 필수 키는 score(0~1), verdict('pass' 또는 'retry'), "
        "issues(문제 요약 배열), improved_answer(교정 답변 또는 기존 답변)이다."
    )

    human_prompt = (
        f"질문:\n{question}\n\n"
        f"초안 답변:\n{draft_answer}\n\n"
        f"참고 문맥:\n{context_snippets or '없음'}\n\n"
        "위 기준에 따라 평가하고 JSON 으로만 응답하라."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    fallback_result = {
        "score": 0.0,
        "verdict": "retry",
        "issues": ["LLM 출력 파싱 실패"],
        "improved_answer": draft_answer,
    }

    raw_output = llm.invoke(messages).content
    try:
        eval_result = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        eval_result = fallback_result

    score = eval_result.get("score", fallback_result["score"])
    try:
        score = max(0.0, min(1.0, float(score)))
    except (TypeError, ValueError):
        score = fallback_result["score"]

    verdict = eval_result.get("verdict", fallback_result["verdict"])
    issues = eval_result.get("issues", fallback_result["issues"])
    if isinstance(issues, str):
        issues = [issues]

    improved_answer = (eval_result.get("improved_answer") or draft_answer).strip()

    state["final_answer"] = improved_answer or draft_answer
    state["answer_eval"] = {
        "score": score,
        "verdict": verdict,
        "issues": issues,
        "raw_output": raw_output,
    }
    return state

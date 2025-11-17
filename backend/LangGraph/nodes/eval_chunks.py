import sys, os, json, re
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(str(Path(__file__).resolve().parents[2]))
from initstate import GraphState
from models import load_openai_model

def node_evaluate_chunks(state: GraphState) -> GraphState:
    """데이터베이스에서 추출한 chunk가 질문과 연관되어있는지 평가하는 함수"""
    params = {"model": os.getenv("EVAL_MODEL")}
    llm = load_openai_model(params_key=tuple(sorted(params.items())))
    evaluated_chunks = []
    chunks = state["chunks"]
    for chunk in chunks:
        content = chunk.get("content", "")
        message = [
            SystemMessage(
                content=(
                    "너는 사용자의 질문과 지식 청크 사이의 관련도를 평가하는 심사관이다. "
                    "각 청크가 질문에 답을 주는 데 얼마나 직접적으로 도움이 되는지를 0에서 1 사이의 점수로 산출하라. "
                    "점수 기준은 다음과 같다:\n"
                    "- 0.75~1.0: 질문 의도를 구체적으로 다루거나 답변의 핵심 근거가 된다.\n"
                    "- 0.4~0.74: 부분적으로 도움이 되거나 배경 지식 수준이다.\n"
                    "- 0.0~0.39: 거의 혹은 전혀 관련이 없다.\n"
                    "판단 시 질문의 요구사항, 키워드, 맥락을 모두 고려하고 추측으로 높은 점수를 주지 마라. "
                    "출력은 반드시 JSON 문자열로 반환하며, 형식은 "
                    "{\"score\": <0~1 사이 실수>, \"reason\": \"간단한 근거\"} 이어야 한다."
                )
            ),
            HumanMessage(
                content=(
                    f"질문: {state['question']}\n\n"
                    f"청크 내용:\n{content}\n\n"
                    "이 청크의 관련도를 평가해 주세요."
                )
            ),
        ]
        raw = llm.invoke(message).content
        parsed = {"score": 0.0, "reason": "LLM output parsing 실패"}
        raw_text = (raw or "").strip()
        if "```" in raw_text:
            code_match = re.search(r'```(?:json)?\s*({.*?})\s*```', raw_text, re.DOTALL)
            if code_match:
                raw_text = code_match.group(1).strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            score_match = re.search(r'["\']?score["\']?\s*:\s*([0-9.]+)', raw_text, re.IGNORECASE)
            reason_match = re.search(r'["\']?reason["\']?\s*:\s*["\']([^"\']+)["\']', raw_text, re.IGNORECASE)
            if score_match:
                parsed = {
                    "score": float(score_match.group(1)),
                    "reason": reason_match.group(1) if reason_match else raw_text[:120],
                }
            else:
                parsed = {"score": 0.2, "reason": f"LLM 출력 파싱 실패 (raw: {raw_text[:80]}…)"}

        eval_score = float(parsed.get("score", 0.0))
        eval_reason = parsed.get("reason", "")

        chunk_with_eval = {
            **chunk,
            "eval_score": eval_score,
            "eval_reason": eval_reason,
        }
        evaluated_chunks.append(chunk_with_eval)

    sorted_chunks = sorted(evaluated_chunks, key=lambda ch: ch.get("eval_score", 0.0), reverse=True)
    min_score = float(os.getenv("CHUNK_MIN_SCORE", "0.5"))
    filtered_chunks = [ch for ch in sorted_chunks if ch.get("eval_score", 0.0) >= min_score]
    if not filtered_chunks:
        filtered_chunks = sorted_chunks[:5]
    state["final_chunks"] = filtered_chunks[:5]
    state["citations"] = [
        ch.get("metadata", {}) for ch in state["final_chunks"]
    ]
    return state

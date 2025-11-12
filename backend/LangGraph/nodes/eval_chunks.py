import sys, os, json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(str(Path(__file__).resolve().parents[2]))
from ..initstate import GraphState
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
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"score": 0.0, "reason": "LLM output parsing 실패"}

        eval_score = float(parsed.get("score", 0.0))
        eval_reason = parsed.get("reason", "")

        chunk_with_eval = {
            **chunk,
            "eval_score": eval_score,
            "eval_reason": eval_reason,
        }
        evaluated_chunks.append(chunk_with_eval)

    sorted_chunks = sorted(evaluated_chunks, key=lambda ch: ch.get("eval_score", 0.0), reverse=True)
    state["final_chunks"] = sorted_chunks[:5]
    state["citations"] = [
        ch.get("metadata", {}) for ch in state["final_chunks"]
    ]
    return state

# backend/LangGraph/nodes/generate_answer.py
from typing import List
from initstate import GraphState
from models import load_openai_model
from langchain_core.messages import HumanMessage, SystemMessage

def _join_context(chunks: List[dict]) -> str:
    """청크 리스트를 사람이 읽기 쉬운 컨텍스트 블록으로 변환"""
    if not chunks:
        return "(관련 컨텍스트 없음)"
    lines = []
    for i, ch in enumerate(chunks, start=1):
        content = ch.get("content", "").strip()
        score = ch.get("eval_score", ch.get("score", None))
        score_str = f" (score: {score:.2f})" if isinstance(score, (int, float)) else ""
        lines.append(f"[{i}] {content}{score_str}")
    return "\n\n".join(lines)

def generate_answer(state: GraphState) -> GraphState:
    """
    ✅ ft_model 역할:
    - RAG 결과(final_chunks) + (재작성된) 질문을 바탕으로
    - 파인튜닝된 OpenAI 챗모델을 호출해 최종 답변을 생성
    - performance_analysis_agent 예시처럼 System/Human 메시지 분리, invoke(messages) 사용
    """

    # 1) 모델 로드 (환경에 맞게 모델명만 바꿔쓰면 됨)
    #    예: "ft:gpt-4o-mini-2024-XX-XX" 또는 사내 FT 모델명
    # ✅ 파인튜닝 large 모델 예시
    params = {
        "model": "ft:gpt-4o-large-2024-11-01",  # 또는 실제 너의 FT 모델명
        "temperature": 0.3
    }

    llm = load_openai_model(params_key=tuple(sorted(params.items())))

    # 2) 컨텍스트 및 질문 준비                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
    context = _join_context(state.get("final_chunks", []))
    question = (state.get("generate_question") or state.get("question") or "").strip()

    # 3) 메시지 구성 (참고 예시의 톤/구조 차용)
    messages = [
        SystemMessage(content="""
당신은 신뢰도 높은 전문가 어시스턴트입니다.
규칙:
- 제공된 '문맥' 안에서만 답변하되, 불명확하면 모르는 부분은 명시
- 근거는 문맥 표현을 요약/인용해 자연스럽게 녹여 설명
- 불필요한 반복 금지, 핵심부터 간결하게
- 항목이 여러 개면 번호/불릿으로 구조화
- 한국어로 답변
        """.strip()),
        HumanMessage(content=f"""
[문맥]
{context}

[질문]
{question}

요청:
- 위 문맥을 근거로 정확하고 간결한 최종 답변을 작성
- 필요시 짧은 근거/사유를 함께 제시
        """.strip())
    ]

    # 4) 모델 호출
    response = llm.invoke(messages)
    answer = (response.content or "").strip()

    # 5) 상태 업데이트
    state["answer"] = answer
    state["final_answer"] = answer

    # 6) 간단 로그
    print("[ft_model(generate_answer)] 최종 답변 생성 완료")

    return state

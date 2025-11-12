from initstate import GraphState

def evaluate_question_answer(state: GraphState) -> GraphState:
    passfrom initstate import GraphState
from models import load_openai_model
from langchain_core.messages import SystemMessage, HumanMessage
import json

def evaluate_question_answer(state: GraphState) -> GraphState:
    """
    ✅ generate_answer 단계에서 생성된 답변을 평가하는 노드
    - 정확성(Accuracy)
    - 충실도(Faithfulness)
    - 관련성(Relevance)
    기준으로 점수를 0~1 사이로 산출하고, 개선 피드백까지 제시
    """

    # 1️⃣ 평가용 모델 로드 (빠른 응답 위해 gpt-4o-mini 권장)
    params = {"model": "gpt-4o-mini", "temperature": 0}
    llm = load_openai_model(params_key=tuple(sorted(params.items())))

    # 2️⃣ 필요한 데이터 준비
    question = state.get("question", "")
    answer = state.get("final_answer", "")
    context = "\n\n".join(ch.get("content", "") for ch in state.get("final_chunks", []))

    # 3️⃣ 메시지 구성 (System + Human)
    messages = [
        SystemMessage(content="""
당신은 답변 품질 평가 전문가입니다.
주어진 문맥(context), 질문, 답변을 비교하여 다음 기준으로 평가하세요:

- 정확성(Accuracy): 답변이 문맥 정보와 일치하고 오류가 없는가?
- 충실도(Faithfulness): 문맥을 벗어나거나 과장된 내용이 없는가?
- 관련성(Relevance): 질문의 의도와 직접적으로 연관되어 있는가?

결과를 반드시 JSON 형식으로 출력하세요:
{
    "accuracy": 0~1 사이 숫자,
    "faithfulness": 0~1 사이 숫자,
    "relevance": 0~1 사이 숫자,
    "feedback": "짧고 명확한 개선 제안"
}
        """.strip()),

        HumanMessage(content=f"""
[문맥]
{context}

[질문]
{question}

[답변]
{answer}

이 답변을 위 기준에 따라 평가하고, 개선 피드백을 JSON으로 반환하세요.
        """.strip()),
    ]

    # 4️⃣ 모델 호출
    response = llm.invoke(messages)
    raw = (response.content or "").strip()

    # 5️⃣ 결과 파싱
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "accuracy": 0,
            "faithfulness": 0,
            "relevance": 0,
            "feedback": f"LLM 응답 파싱 실패: {raw[:150]}",
        }

    # 6️⃣ state 업데이트
    state["evaluation"] = result

    # 7️⃣ 로그 출력
    print("[eval_generated_answer] QA 평가 완료 ✅")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return state

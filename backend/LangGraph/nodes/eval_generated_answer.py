from backend.LangGraph.initstate import GraphState
from typing_extensions import TypedDict, NotRequired
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

import os
import json

# ---------------------------
# 1. State 정의
# ---------------------------
class GraphState(TypedDict):
    # 유저가 입력한 원문
    question: str
    # LLM이 생성한 최종 답변
    final_answer: str

    # 아래 두 개는 평가 에이전트가 채워줄 값
    similarity_score: NotRequired[float]   # 0~100 점수
    similarity_comment: NotRequired[str]   # 왜 그렇게 판단했는지 설명


# ---------------------------
# 2. OpenAI 설정
# ---------------------------
dotenv_path = find_dotenv()
if not dotenv_path:
    raise RuntimeError('.env 파일을 찾을 수 없습니다.')
load_dotenv(dotenv_path)

OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.0'))  # 기본 0으로 설정
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    raise RuntimeError('OPENAI_API_KEY 환경 변수가 설정되어 있어야 합니다.')

client = OpenAI(api_key=OPENAI_API_KEY)

params = {
    'model': OPENAI_MODEL,
    'temperature': temperature,
}


# ---------------------------
# 3. LLM 호출 함수: 유사도 평가
# ---------------------------
def llm_evaluate_similarity(user: str, final_answer: str) -> dict:
    """
    user(사용자 질문/요구사항)와 final_answer(모델의 최종 답변)를 비교해서
    유사도 점수와 코멘트를 JSON 형태로 돌려주는 함수.

    리턴 예시:
    {
        "score": 92.5,
        "comment": "질문의 의도와 거의 일치하며, 세부 설명도 충분합니다."
    }
    """

    system_prompt = """
너는 질문과 답변의 일치도를 평가하는 심사위원이다.
다음 기준으로 평가해라.

- score: 0~100 사이의 숫자 (질문 의도와 답변 내용이 얼마나 잘 맞는지)
- comment: 한국어로 간단한 설명 (어떤 점이 좋고, 어떤 점이 부족한지)

반드시 아래와 같은 JSON 형식으로만 답해라:

{
  "score": <숫자>,
  "comment": "<설명>"
}
    """.strip()

    user_prompt = f"""
[사용자 요청]

{user}

[모델 최종 답변]

{final_answer}
    """.strip()

    response = client.chat.completions.create(
        **params,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content.strip()

    # 모델이 JSON 문자열을 돌려줬다고 가정하고 파싱
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # 혹시 JSON 형식이 살짝 틀어져도 죽지 않게 기본값 처리
        data = {
            "score": 0.0,
            "comment": f"JSON 파싱 실패. 원본 응답: {content}",
        }

    # 안전하게 기본값 보정
    score = float(data.get("score", 0.0))
    comment = str(data.get("comment", ""))

    return {"score": score, "comment": comment}


# ---------------------------
# 4. 평가 에이전트(노드)
# ---------------------------
def evaluate_similarity_agent(state: GraphState) -> GraphState:
    """
    state 안의 user, final_answer를 사용해서
    유사도 점수 + 코멘트를 계산하고,
    그 결과를 다시 state에 넣어주는 에이전트.
    """

    user = state["question"]
    final_answer = state["final_answer"]

    result = llm_evaluate_similarity(user, final_answer)

    state["similarity_score"] = result["score"]
    state["similarity_comment"] = result["comment"]

    return state


# ---------------------------
# 5. 사용 예시 (테스트용)
# ---------------------------
if __name__ == "__main__":
    # 예시 state
    state: GraphState = {
        "question": "나는 노래 부르는 걸 좋아해 전공을 어디로 가면 좋을까?.",
        "final_answer": "노래 부르는것을 좋아한다면 실용음악과를 추천해드려요.",
    }

    new_state = evaluate_similarity_agent(state)

    print("유사도 점수:", new_state["similarity_score"])
    print("평가 코멘트:", new_state["similarity_comment"])


def evaluate_question_answer(state: GraphState) -> GraphState:
    pass
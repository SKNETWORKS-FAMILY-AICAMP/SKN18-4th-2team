# 1. LLM 기반 질문과, 추출된 chunk의 맥락상 유사도를 평가
import sys, os, json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

sys.path.append(str(Path(__file__).resolve().parents[2]))
from models import load_openai_model


def evaluate_interview_chunk_relevance(question: str, chunk_content: str) -> dict:
    """면접 질문과 chunk 간의 맥락상 유사도를 평가하는 agent
    
    .env에서 설정을 읽어옵니다:
    - OPENAI_API_KEY: OpenAI API Key (자동 로드)
    - EVAL_MODEL: 평가용 OpenAI 모델명 (기본값: gpt-4o-mini)
    - EVAL_TEMPERATURE: 생성 온도 (기본값: 0.1)
    
    Args:
        question: 사용자의 면접 관련 질문
        chunk_content: 평가할 chunk의 내용
    
    Returns:
        dict: {"score": float, "reason": str} 형태의 평가 결과
    """
    # .env에서 모델 설정 읽기
    model_name = os.getenv("EVAL_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("EVAL_TEMPERATURE", "0.1"))
    
    params = {"model": model_name, "temperature": temperature}
    llm = load_openai_model(params_key=tuple(sorted(params.items())))
    
    message = [
        SystemMessage(
            content=(
                "너는 면접 준비와 관련된 질문과 지식 청크 사이의 맥락적 관련도를 평가하는 전문가이다. "
                "각 청크가 면접 질문에 답하는 데 얼마나 직접적이고 실용적인 도움이 되는지를 0에서 1 사이의 점수로 산출하라. "
                "면접 맥락을 고려하여 다음 기준으로 평가하라:\n"
                "- 0.75~1.0: 질문에 대한 구체적인 답변 내용이 포함되어 있거나, 면접 상황에서 직접 활용 가능한 핵심 정보다.\n"
                "- 0.4~0.74: 부분적으로 관련이 있거나 배경 지식 수준이며, 간접적으로 도움이 된다.\n"
                "- 0.0~0.39: 면접 질문과 거의 또는 전혀 관련이 없다.\n"
                "판단 시 질문의 의도, 면접 맥락, 키워드 일치도를 종합적으로 고려하고, 추측으로 높은 점수를 주지 마라. "
                "출력은 반드시 JSON 문자열로 반환하며, 형식은 "
                "{\"score\": <0~1 사이 실수>, \"reason\": \"평가 근거\"} 이어야 한다."
            )
        ),
        HumanMessage(
            content=(
                f"면접 질문: {question}\n\n"
                f"청크 내용:\n{chunk_content}\n\n"
                "이 청크가 면접 질문에 답하는 데 얼마나 관련이 있는지 평가해 주세요."
            )
        ),
    ]
    
    raw = llm.invoke(message).content
    
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"score": 0.0, "reason": "LLM output parsing 실패"}
    
    return {
        "score": float(parsed.get("score", 0.0)),
        "reason": parsed.get("reason", "")
    }

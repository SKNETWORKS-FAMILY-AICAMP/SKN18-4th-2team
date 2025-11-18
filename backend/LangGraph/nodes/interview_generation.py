# 최종 답변 생성 노드 -> 
# 면접질문 추천 쿼리 -> 답변 시, 질문에 대함 답변을 같이 추출하지 말고, 관련 질문만 추천해줘
# 답변 수정 쿼리의 -> 답변 시, vectorDB의 답변들과 비교에서 차이가 나는 부분이 찾고 , 추천답변 작성 
# -> 서치된 답변에 대한 question_intent를 찾고 이를 기반으로 -> 같은 유형의 질문을 추천 아니면 다른 질문 유형을 추천하도록
import sys, os
from pathlib import Path
from collections import Counter

from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

sys.path.append(str(Path(__file__).resolve().parents[2]))
from initstate import GraphState
from models import load_openai_model


def interview_generation_node(state: GraphState) -> GraphState:
    """면접 관련 최종 답변을 생성하는 노드
    
    질문 유형에 따라 다른 응답 생성:
    1. question_recommendation (질문 추천):
    - 관련 면접 질문만 추천 (answers는 포함하지 않음)
    - chunk에서 추출한 question_intent 기반으로 유사/다른 유형 질문 추천
    
    2. answer_feedback (답변 피드백):
    - VectorDB의 답변들과 비교하여 차이점 분석
    - 추천 답변 작성
    - question_intent 기반으로 유사/다른 질문 유형 추천
    """
    # .env에서 모델 설정 읽기
    model_name = os.getenv("GEN_MODEL", "gpt-4o")
    temperature = float(os.getenv("GEN_TEMPERATURE", "0.2"))
    
    params = {"model": model_name, "temperature": temperature}
    llm = load_openai_model(params_key=tuple(sorted(params.items())))
    
    question = state.get("question", "")
    final_chunks = state.get("final_chunks", [])
    query_type = state.get("interview_query_type", "answer_feedback")
    
    # chunk에서 question_intent 추출 및 분석
    question_intents = []
    for chunk in final_chunks:
        metadata = chunk.get("metadata", {})
        intent = metadata.get("question_intent")
        if intent:
            question_intents.append(intent)
    
    # 가장 많이 나온 question_intent 찾기
    intent_analysis = ""
    if question_intents:
        intent_counts = Counter(question_intents)
        most_common_intent = intent_counts.most_common(1)[0][0]
        intent_analysis = f"\n검색된 답변의 주요 질문 유형: {most_common_intent} (총 {len(question_intents)}개 중 {intent_counts[most_common_intent]}개)"
    else:
        most_common_intent = None
    
    # chunk 내용을 문자열로 결합 (메타데이터 포함)
    chunks_text = "\n\n".join([
        f"[청크 {i+1}]\n"
        f"- 직군: {chunk.get('metadata', {}).get('occupation', 'N/A')}\n"
        f"- 질문 유형: {chunk.get('metadata', {}).get('question_intent', 'N/A')}\n"
        f"{chunk.get('content', '')}" 
        for i, chunk in enumerate(final_chunks)
    ])
    
    if query_type == "question_recommendation":
        # 질문 추천 모드
        intent_instruction = ""
        if most_common_intent:
            intent_instruction = (
                f"\n주요 질문 유형: {most_common_intent}\n"
                "- 이 유형과 유사한 질문을 3개 추천하라\n"
            )
        
        message = [
            SystemMessage(
                content=(
                    "너는 면접 준비를 돕는 전문 컨설턴트이다.\n\n"
                    "**핵심 규칙:**\n"
                    "- 청크의 텍스트를 그대로 사용하라 (수정/추가 금지)\n"
                    "- 새로운 질문을 지어내지 마라\n\n"
                    "출력 형식:\n"
                    "1. 총 3개의 면접 질문을 번호와 함께 나열\n"
                    "2. 마지막에 선정 이유를 2문장으로 요약 설명"
                    "3. 답변수정 또는 다른 유형 면접추천 질문을 유도해라"
                    f"{intent_instruction}"
                )
            ),
            HumanMessage(
                content=(
                    f"사용자 요청: {question}\n\n"
                    f"참고 자료:{intent_analysis}\n{chunks_text}\n\n"
                    "청크의 [질문]을 3개 선택하여 추천하고, 선정 이유를 간략히 설명해주세요."
                )
            ),
        ]
    else:
        # 답변 피드백 모드
        intent_guidance = ""
        if most_common_intent:
            intent_guidance = (
                f"\n참고 자료는 주로 '{most_common_intent}' 유형의 질문에 대한 답변들이다. "
                "이 유형의 특성을 고려하여 답변을 작성하고, "
                "마지막에 같은 유형의 유사 질문 2개와 다른 유형의 연습 질문 2개를 추천하라."
            )
        
        message = [
            SystemMessage(
                content=(
                    "너는 면접 답변을 평가하고 개선하는 전문 컨설턴트이다.\n\n"
                    "**핵심 규칙:**\n"
                    "1. 반드시 제공된 청크의 [당변] 텍스트를 기반으로 작성하라\n"
                    "2. 청크에 없는 내용을 절대 지어내지 마라\n"
                    "3. 청크가 비어있거나 관련성이 낮으면 '관련 데이터 부족'으로 명시\n\n"
                    "출력 형식:\n"
                    "1. 추천 답변: [청크의 [답변] 내용을 분석하여 재구성]\n"
                    "2. 핵심 포인트: [청크에서 추출한 주요 키워드 3-5개]\n"
                    "3. 참고 자료 분석: [청크의 답변 패턴과 특징]\n"
                    "   - 공통점: [청크의 답변들에서 공통적으로 나타나는 요소]\n"
                    "   - 차이점: [각 청크의 다른 접근 방식이나 강조점]\n"
                    "   - 개선 포인트: [청크를 기반으로 한 개선 제안]\n"
                    "4. 추가 연습 질문: [청크의 직군/유형과 유사한 질문 2개과 직군 동일/다른 유형의 연습 질문]"
                    f"{intent_guidance}"
                )
            ),
            HumanMessage(
                content=(
                    f"면접 질문: {question}\n\n"
                    f"참고 자료:{intent_analysis}\n{chunks_text}\n\n"
                    "위 청크의 [답변] 내용을 분석하여 추천 답변을 작성해주세요. "
                    "청크가 비어있거나 관련성이 낮다면 '관련 데이터가 부족합니다'라고 명시하세요."
                )
            ),
        ]
    
    raw_answer = llm.invoke(message).content
    state["final_answer"] = raw_answer
    
    return state

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
    
    # chunk 내용을 문자열로 결합
    # metadata는 vector_search에서 이미 포함되어 있음
    chunks_text = "\n\n".join([
        f"[청크 {i+1}]\n{chunk.get('content', '')}" 
        for i, chunk in enumerate(final_chunks)
    ])
    
    if query_type == "question_recommendation":
        # 질문 추천 모드
        intent_instruction = ""
        if most_common_intent:
            intent_instruction = (
                f"\n주요 질문 유형: {most_common_intent}\n"
                "- 이 유형과 유사한 질문을 5개 추천하라\n"
                "- 추가로 다른 유형의 질문을 3개 추천하여 다양성을 제공하라"
            )
        
        message = [
            SystemMessage(
                content=(
                    "너는 면접 준비를 돕는 전문 컨설턴트이다. "
                    "사용자의 요청에 따라 적절한 면접 질문들을 추천해야 한다.\n\n"
                    "출력 규칙:\n"
                    "1. 질문만 추천하고, 답변은 포함하지 마라\n"
                    "2. 제공된 청크에서 question_intent를 분석하여 유사한 유형의 질문과 다른 유형의 질문을 추천하라\n"
                    "3. 총 5개 정도의 면접 질문을 추천하라\n"
                    "4. 각 질문은 번호를 매겨서 명확하게 구분하라\n"
                    "5. 질문 유형별로 그룹화하여 제시하라"
                    f"{intent_instruction}"
                )
            ),
            HumanMessage(
                content=(
                    f"사용자 요청: {question}\n\n"
                    f"참고 자료:{intent_analysis}\n{chunks_text}\n\n"
                    "위 정보를 바탕으로 관련 면접 질문들을 추천해 주세요."
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
                "마지막에 같은 유형의 유사 질문 2~3개와 다른 유형의 연습 질문 2~3개를 추천하라."
            )
        
        message = [
            SystemMessage(
                content=(
                    "너는 면접 답변을 평가하고 개선하는 전문 컨설턴트이다. "
                    "사용자의 면접 질문에 대한 적절한 답변을 제시하고, "
                    "참고 자료와 비교하여 차이점을 분석하라.\n\n"
                    "출력 형식:\n"
                    "1. 추천 답변: [구체적인 답변 내용]\n"
                    "2. 핵심 포인트: [중요한 키워드나 구조]\n"
                    "3. 참고 자료 분석:\n"
                    "   - 공통점: [참고 답변들에서 공통적으로 나타나는 요소]\n"
                    "   - 차이점: [각 답변들의 다른 접근 방식이나 강조점]\n"
                    "   - 개선 포인트: [더 나은 답변을 위한 제안]\n"
                    "4. 추가 연습 질문: [같은 유형 2~3개, 다른 유형 2~3개 추천]"
                    f"{intent_guidance}"
                )
            ),
            HumanMessage(
                content=(
                    f"면접 질문: {question}\n\n"
                    f"참고 자료:{intent_analysis}\n{chunks_text}\n\n"
                    "위 정보를 바탕으로 적절한 답변을 작성하고, 참고 자료들을 분석하여 차이점과 개선 포인트를 제시해 주세요."
                )
            ),
        ]
    
    raw_answer = llm.invoke(message).content
    state["final_answer"] = raw_answer
    
    return state

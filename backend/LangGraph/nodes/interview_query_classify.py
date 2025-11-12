# 1. interview_query_classify_agent.py에서 생성한 agent를 불러옴
# 2. 질문유형에 따른 sql filtering 여부를 여기서 넣을지 뭐가 좋은 지 확인해봐야함.
#
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from initstate import GraphState
from agent.interview_query_classify_agent import classify_interview_query_type


def interview_query_classify_node(state: GraphState) -> GraphState:
      """면접 관련 질문의 유형을 분류하는 노드
      
      주의: classify 노드에서 category가 '면접'으로 분류된 후,
            그래프 라우팅에 의해 이 노드로 연결됩니다.
      
      interview_query_classify_agent를 사용하여:
      1. 질문 추천(question_recommendation) vs 답변 피드백(answer_feedback) 분류
      2. 질문 추천일 경우 키워드 추출
      
      분류 결과를 state에 저장하여 후속 노드에서 활용
      - question_recommendation: SQL 필터링 -> VectorDB 검색
      - answer_feedback: 직접 VectorDB 검색
      """
      question = state.get("question", "")
      
      # agent를 호출하여 질문 유형 분류
      classification_result = classify_interview_query_type(question)
      
      # 분류 결과를 state에 저장
      state["interview_query_type"] = classification_result["query_type"]
      state["interview_keywords"] = classification_result["keywords"]
      state["classification_reason"] = classification_result["reason"]
      
      return state

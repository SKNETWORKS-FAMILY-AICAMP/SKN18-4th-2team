# 면접 LangGraph 개요

## 1. 전체 워크플로우
- 사용자 입력 → `classify_category`(면접/대학진로 분기) → `interview_query_classify_node`
- 면접일 경우:
  1. 질문 유형 분류(`question_recommendation` 또는 `answer_feedback`) 및 키워드 추출
  2. `interview_vector_search_node`에서 SQL 필터링 + 벡터 검색
  3. `interview_eval_node`가 LLM으로 관련도 평가 후 상위 chunk 선정
  4. `interview_generation_node`가 최종 응답 생성

## 2. 분류 및 키워드 추출
- 정규식 기반 패턴으로 질문 유형 분류 (LLM 미사용, <1ms)
  - 질문 추천 패턴: “질문 추천”, “예상 질문” 등
  - 답변 피드백 패턴: “어떻게 대답”, “좋은 답변” 등
- 60+ 면접 도메인 키워드 추출 (직무, 기술, 면접 유형, 주제)
  - 불용어 제거 후 최대 10개 반환
  - 결과 구조: `{ query_type, keywords, reason }`

## 3. 메타데이터 & SQL 필터링
- Embedding 데이터 메타데이터
  - `occupation`: ARD, BM, ICT, MM, PS, RND, SM
  - `question_intent`: motivation_fit, self_reflection 등 16개
- 키워드 매핑으로 SQL 필터 생성  
  `filter = { "occupation": "ICT", "question_intent": "mechanism_reason" }`
- `vectorstore.similarity_search(query, k=5, filter=filter)`  
  필터 없으면 일반 벡터 검색으로 폴백

## 4. 노드별 책임
| 단계 | 노드 | 모델 | 역할 |
| --- | --- | --- | --- |
|1|`classify_category`|ChatOllama|면접/대학진로 분류|
|2|`interview_query_classify_node`|없음|패턴 기반 유형 분류, 키워드 추출|
|3|`interview_vector_search_node`|Embedding|SQL+벡터 검색|
|4|`interview_eval_node`|ChatOpenAI (EVAL_MODEL)|chunk 관련도 평가(0~1)|
|5|`interview_generation_node`|ChatOpenAI (GEN_MODEL)|질문 추천 또는 답변 생성|

## 5. 상태(State) 흐름
```python
# 초기
{ "user": "...", "question": "..." }

# 분류 후
{ ..., "category": "면접" }

# 질문 유형 분류 후
{
  ..., "interview_query_type": "question_recommendation",
  "interview_keywords": ["백엔드", "개발자"],
  "classification_reason": "질문 추천 패턴 감지..."
}

# 검색 후
{ ..., "chunks": [{ "content": "...", "metadata": {...}, "score": 0.85 }, ...] }

# 평가 후
{ ..., "final_chunks": [{ "content": "...", "eval_score": 0.92, "eval_reason": "..." }, ...] }

# 생성 후
{ ..., "final_answer": "1. ...\n2. ..." }
```

## 6. 비용/성능 (평균)
- 전체 5~12초 / 요청당 약 $0.025
- LLM 사용: `classify_category`, `interview_eval_node`, `interview_generation_node`
- Non-LLM: 질문 분류, 키워드 추출, SQL+벡터 검색

## 7. 환경 변수 요약
```bash
# LLM
OLLAMA_MODEL=llama3.1
EVAL_MODEL=gpt-4o-mini
GEN_MODEL=gpt-4o
GEN_TEMPERATURE=0.2

# Embedding
EMBEDDING_BACKEND=huggingface
LOCAL_EMBEDDING_MODEL=jhgan/ko-sbert-sts
LOCAL_EMBEDDING_NORMALIZE=true
LOCAL_EMBEDDING_DIM=768

# PostgreSQL VectorDB
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=skn4th
POSTGRES_PASSWORD=sk4th1234
POSTGRES_DB=skn4th_db
```

## 8. 테스트 시나리오
1. **질문 추천**: “백엔드 개발자 기술면접 질문 추천해주세요”  
   → query_type=question_recommendation, ICT+mechanism_reason 필터, 질문 목록 반환
2. **답변 피드백**: “자기소개 어떻게 하면 좋을까요?”  
   → query_type=answer_feedback, chunk 평가 후 추천 답변+포인트+차이점 생성

## 9. 확장 포인트
- 키워드/패턴 추가로 분류 확장
- question_intent 자동 라벨링 개선
- 결과 캐싱 및 평가 지표 도입
- SQL 필터 다중 조건(or) 지원, TF-IDF 기반 키워드 가중치 등

## 10. 테스트 질문 결과
================================================================================
테스트: 질문 추천
================================================================================
사용자: 취업 준비생, 소프트웨어 개발자 지망
질문: 백엔드 개발자 면접에서 자주 나오는 질문들을 추천해 주세요

실행 중...

C:\dev\study\4th_mini_project\SKN18-4th-2team\backend\models.py:54: LangChainDeprecationWarning: The class `ChatOllama` was deprecated in LangChain 0.3.1 and will be removed in 1.0.0. An updated version of the class exists in the `langchain-ollama package and should be used instead. To use it run `pip install -U `langchain-ollama` and import as `from `langchain_ollama import ChatOllama``.
  return ChatOllama(model=model, temperature=temperature)
--------------------------------------------------------------------------------
결과:
--------------------------------------------------------------------------------
카테고리: 면접

면접 질문 유형: question_recommendation
추출된 키워드: ['추천해', '자주', '나오는', '개발자', '개발', '면접에서', '질문들을', '백엔드']
분류 이유: 질문 추천 패턴 감지 (2개): '질문', '추천', '알려' 등의 표현 포함

검색된 청크 수: 0
최종 선택된 청크 수: 0

--------------------------------------------------------------------------------
최종 답변:
--------------------------------------------------------------------------------
### 기술적 질문

1. 백엔드 아키텍처를 설계할 때 고려해야 할 주요 요소는 무엇인가요?
2. RESTful API를 설계할 때 주의해야 할 점은 무엇인가요?
3. 데이터베이스 인덱싱의 장단점에 대해 설명해 주세요.
4. 서버와 클라이언트 간의 인증 및 권한 부여를 어떻게 구현하나요?
5. 마이크로서비스 아키텍처의 장단점에 대해 설명해 주세요.

### 문제 해결 및 사고 과정 질문

1. 서버 성능이 저하되었을 때 문제를 진단하고 해결하는 방법을 설명해 주세요.
2. 새로운 기술을 학습하고 적용할 때 어떤 과정을 거치나요?

### 행동 및 경험 기반 질문

1. 이전 프로젝트에서 가장 도전적이었던 백엔드 문제는 무엇이었고, 어떻게 해결했나요?
2. 팀 내에서 기술적 갈등이 발생했을 때 어떻게 대처했나요?

### 커뮤니케이션 및 협업 질문

1. 프론트엔드 개발자와 협업할 때 중요한 점은 무엇이라고 생각하나요?
2. 비기술적인 이해관계자에게 복잡한 기술적 개념을 설명한 경험이 있나요? 어떻게 설명했나요?

================================================================================
테스트: 답변 피드백
================================================================================
사용자: 취업 준비생, 프론트엔드 개발자 지망
질문: 자기소개를 해달라는 면접 질문에 어떻게 대답하면 좋을까요?

실행 중...

--------------------------------------------------------------------------------
결과:
--------------------------------------------------------------------------------
카테고리: 면접

면접 질문 유형: answer_feedback
추출된 키워드: []
분류 이유: 답변 피드백 패턴 감지 (2개): '어떻게', '대답', '말하면' 등의 표현 포함

검색된 청크 수: 0
최종 선택된 청크 수: 0

--------------------------------------------------------------------------------
최종 답변:
--------------------------------------------------------------------------------
1. 추천 답변: 
"안녕하세요, 저는 [이름]입니다. [전공/경력]을 통해 [관련 분야]에 대한 깊은 이해와 경험을 쌓았습니다. 특히, [특정 프로젝트나 경험]을 통해 [구체적인 성과나 배운 점] 을 얻었습니다. 이러한 경험을 바탕으로 [지원하는 회사/직무]에서 [기여할 수 있는 점]을 발휘하고 싶습니다. 제 [특정 강점이나 기술]은 팀과 함께 [목표]를 달성하는 데 큰 도움이 될 것입니다. 감사합니다."

2. 핵심 포인트:
   - 이름 및 간단한 배경 소개
   - 관련 전공이나 경력 강조
   - 구체적인 경험과 성과
   - 지원 직무와의 연관성
   - 강점 및 기여 가능성

3. 참고 자료 분석:
   - 공통점: 대부분의 답변은 개인의 배경과 경력을 간단히 소개하고, 지원하는 직무와의 관련성을 강조합니다. 또한, 구체적인 경험이나 성과를 언급하여 신뢰성을 높입니다.
   - 차이점: 어떤 답변은 개인의 성격이나 가치관을 강조하기도 하고, 다른 답변은 기술적 능력이나 특정 프로젝트의 성공 사례에 집중하기도 합니다.
   - 개선 포인트: 답변을 더 매력적으로 만들기 위해서는 지원하는 회사의 가치나 문화에 맞춘 개인적인 열정이나 목표를 추가하는 것이 좋습니다. 또한, 구체적인 수치나 결과를 포함하여 성과를 명확히 하는 것이 중요합니다.

4. 추가 연습 질문:
   - 같은 유형:
     1. "자신의 강점과 약점에 대해 말해보세요."
     2. "최근에 해결한 문제에 대해 설명해 주세요."
     3. "왜 이 회사에 지원하게 되었나요?"
   - 다른 유형:
     1. "5년 후 자신의 모습을 어떻게 상상하나요?"
     2. "팀에서 갈등을 해결한 경험이 있나요?"
     3. "어떤 상황에서 가장 큰 성취감을 느끼나요?"

# from node.classify 에 이후 노드임.
#면접관련 langraph로 이동 후
# 1. 분야나 질문의도에 따른 질문 추천인지
# 2. 답변 관련인지 질문을 판별(적절한 답변을 물어보는 건지)
# 3. 질문 추천이면 -> query-keyword 추출 후  sql-filtering -> 필터링 된것만만 vectorDB search
# 4. 답변질문이면 -> vectorDB search

import re
from typing import List, Set


# 질문 추천 패턴
QUESTION_RECOMMENDATION_PATTERNS = [
    # 질문 추천 키워드
    r'질문.*추천',
    r'추천.*질문',
    r'어떤.*질문',
    r'질문.*알려',
    r'알려.*질문',
    r'예상.*질문',
    r'질문.*목록',
    r'면접.*예상',
    r'물어본다',
    r'물어볼',
    r'나오는.*질문',
]

# 답변 피드백 패턴
ANSWER_FEEDBACK_PATTERNS = [
    r'어떻게.*대답',
    r'대답.*방법',
    r'답변.*하',
    r'말하면',
    r'어떻게.*하면',
    r'하는.*방법',
    r'하는.*게',
    r'좋은.*대답',
    r'적절한.*답변',
    r'조언',
]

# 키워드 추출을 위한 면접 관련 도메인 키워드
# OCCUPATION_MAPPING + QUESTION_INTENT_MAPPING의 모든 키워드 포함
INTERVIEW_DOMAIN_KEYWORDS = {
    # ===== OCCUPATION 키워드 (7개 코드) =====
    # ARD - 예술/디자인
    '예술', '디자인', 'UI', 'UX', '창의', '그래픽',
    
    # BM - 비즈니스/경영
    '비즈니스', '경영', '기획', '전략', '마케팅', '영업', 
    'PM', 'PO', '프로젝트 매니저', '프로덕트 매니저',
    '프로젝트매니저', '프로덕트매니저',
    
    # ICT - IT/개발
    '개발자', '개발', '프로그래밍', '코딩', '프론트엔드', '백엔드', '풀스택',
    '소프트웨어', 'Java', 'Python', 'JavaScript', 'C++', 'React', 'Vue', 
    'Spring', 'Django', 'Flask', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 
    '클라우드', '데브옥스',
    
    # MM - 재무/회계
    '재무', '회계', '재무관리', '회계사', '세무', '예산', '재정',
    
    # PS - 생산/제조
    '생산', '제조', '생산관리', '품질관리', '공장', '공정', '생산성',
    
    # RND - 연구개발
    '연구', '개발', '연구개발', 'R&D', '연구원', '기술개발', '신기술', '특허',
    'AI', '머신러닝', '데이터', '데이터분석', '데이터 사이언스', '데이터사이언스',
    
    # SM - 영업/판매
    '영업', '판매', '마케팅', '세일즈', '영업관리', '고객', '세일즈 마케팅',
    
    # ===== QUESTION_INTENT 키워드 (16개 코드) =====
    # 1) motivation_fit - 목표/지원동기/선호/희망부서
    '목표', '지원동기', '지원', '동기', '포부', '우리회사', '적합',
    '우선순위', '중점적', '선호', '희망부서', '희망', '부서',
    '가고싶은', '회사', '선호부서',
    
    # 2) self_reflection - 후회/장단점/자기소개/자신있는
    '후회', '강점', '약점', '장점', '단점', '자기소개', '자기',
    '스스로', '자신있는', '수준', '숙련', '레벨', '대표적',
    '프로젝트', '반성', '성찰', '학습', '성장',
    
    # 3) criteria_evaluation - 중요하게 생각/기준/평가척도
    '기준', '평가척도', '평가', '판단기준', '판단', '선정기준',
    '품질기준', '품질', '중요하게', '생각', '기준점', '측정',
    
    # 4) stakeholder_comm - 협업/갈등/커뮤니케이션/조율
    '협업', '갈등', '소통', '설듵', '보고', '피드백', '커뮤니케이션',
    '이해관계자', '조율', '협력', '팀워크', '팀',
    
    # 5) behavioral_star - 경험/사례/극볹/성과/결과
    '경험', '사례', '극볹', '성과', '결과', '해결', '대응',
    'STAR', 'star', '경험담', '상황', '행동', '어떻게해결', '어떻게대응',
    
    # 6) procedure_method - 어떻게/방법/절차/프로세스
    '어떻게', '방법', '방법론', '절차', '프로세스', '순서',
    '단계', '지침', '절차서', 'how to', 'howto',
    
    # 7) mechanism_reason - 왜/이유/원인/소감/원리
    '왜', '이유', '원인', '배경', '원리', '생각', '소감', '인과',
    '메커니즘', '작동원리', '개념', '동작',
    'OOP', '디자인패턴', '알고리즘', '자료구조', '네트워크',
    '데이터베이스', '기술', '기술면접',
    
    # 8) compare_tradeoff - 비교/장단점/vs/trade-off
    '비교', '장단점', '대안', '차이', 'vs', 'VS', 'trade-off', 'tradeoff',
    '트레이드오프', '선택', '중에', '어느', '더',
    
    # 9) evidence_metric - 지표/수치/실험/검증/AUC/F1
    '지표', '수치', '근거', '증거', '성능', '정확도', '정밀도',
    '재현율', 'F1', 'f1', 'AUC', 'auc', '실험', '검증', 'validation',
    '통계', 'p-value', 'pvalue', '신뢰구간', '성과측정',
    
    # 10) leadership_ownership - 리더십/오너십/주도/책임
    '리더십', '오너십', '주도', '책임', '권한', '위임', '결정',
    '주도적', '주인의식', '이끌어',
    
    # 11) creativity_ideation - 창의/개선/아이디어/정책제안
    '새로운', '혁신', '개선', '아이디어', '창의', '창의성', '창의력',
    '브레인스토밍', '개선방안', '정책제안', '제안', '창조', '발상',
    
    # 12) root_cause - 원인분석/재발방지/디버그/트러블슈팅
    '원인분석', '근본원인', '재발방지', '재발', '트러블슈팅',
    '디버그', '문제해결', '해결', '분석',
    
    # 13) ethics_compliance - 윤리/준법/IRB/GDPR/개인정보
    '윤리', '준법', '컴플라이언스', 'IRB', 'irb', 'GDPR', 'gdpr',
    'HIPAA', 'hipaa', '개인정보', '보안정책', '보안', '법규', '규정', '준수',
    
    # 14) application_transfer - 적용/현장/전이/실무적용/use case
    '적용', '현장', '전이', '다른상황', '다른산업', 'use case', 'usecase',
    '실무적용', '실무', '활용', '응용', '확장',
    
    # 15) estimation_planning - 대략/예상/일정/계획/리소스계획
    '대략', '얼마나', '예상', '추정', '일정', '계획', '납기',
    '스케줄', '리소스계획', '목표기간', '기획', '예측',
    
    # 16) cost_resource - 비용/ROI/예산/원가/효율/가성비
    '비용', 'ROI', 'roi', '예산', '원가', '인력', '장비', '효율',
    '투입대비', '가성비', '비용효율', '자원', '자원관리',
}


def extract_keywords_from_text(text: str) -> List[str]:
    """텍스트에서 면접 관련 키워드를 추출
    
    Args:
        text: 분석할 텍스트
    
    Returns:
        추출된 키워드 리스트
    """
    keywords: Set[str] = set()
    text_lower = text.lower()
    
    # 도메인 키워드 중 텍스트에 포함된 것들 추출
    for keyword in INTERVIEW_DOMAIN_KEYWORDS:
        if keyword.lower() in text_lower or keyword in text:
            keywords.add(keyword)
    
    # 추가적으로 명사형 단어 추출 (한글 2글자 이상)
    # 간단한 패턴 매칭
    korean_words = re.findall(r'[\uac00-\ud7a3]{2,}', text)
    for word in korean_words:
        # 불용어 필터링
        if word not in ['면접', '질문', '대답', '주세요', '알려', '추천', '하면', '어떻게']:
            if len(word) >= 2 and word not in keywords:
                keywords.add(word)
    
    # 영어 단어 추출 (대문자 시작 또는 2글자 이상)
    english_words = re.findall(r'\b[A-Z][a-zA-Z]+\b|\b[a-z]{2,}\b', text)
    for word in english_words:
        if word.lower() not in ['interview', 'question', 'answer']:
            keywords.add(word)
    
    return list(keywords)[:10]  # 최대 10개로 제한


def classify_interview_query_type(question: str) -> dict:
    """면접 관련 질문의 유형을 분류하는 함수 (LLM 사용 없이 패턴 기반)
    
    주의: 이 함수는 classify 노드에서 category가 '면접'으로 분류된 후에만 호출됩니다.
    
    Args:
        question: 사용자의 면접 관련 질문
    
    Returns:
        dict: {
            "query_type": str,  # "question_recommendation" 또는 "answer_feedback"
            "keywords": list,   # 추출된 키워드 리스트 (질문 추천일 경우)
            "reason": str       # 분류 이유
        }
    """
    question_lower = question.lower()
    
    # 1. 질문 추천 패턴 체크
    recommendation_score = 0
    matched_recommendation_patterns = []
    
    for pattern in QUESTION_RECOMMENDATION_PATTERNS:
        if re.search(pattern, question):
            recommendation_score += 1
            matched_recommendation_patterns.append(pattern)
    
    # 2. 답변 피드백 패턴 체크
    feedback_score = 0
    matched_feedback_patterns = []
    
    for pattern in ANSWER_FEEDBACK_PATTERNS:
        if re.search(pattern, question):
            feedback_score += 1
            matched_feedback_patterns.append(pattern)
    
    # 3. 분류 결정
    if recommendation_score > feedback_score:
        query_type = "question_recommendation"
        keywords = extract_keywords_from_text(question)
        reason = f"질문 추천 패턴 감지 ({recommendation_score}개): '질문', '추천', '알려' 등의 표현 포함"
    elif feedback_score > recommendation_score:
        query_type = "answer_feedback"
        keywords = []
        reason = f"답변 피드백 패턴 감지 ({feedback_score}개): '어떻게', '대답', '말하면' 등의 표현 포함"
    else:
        # 동점이거나 둘 다 0일 경우 - 기본적으로 답변 피드백으로 처리
        # 단, '?' 로 끝나고 키워드가 있다면 답변 피드백으로 간주
        query_type = "answer_feedback"
        keywords = []
        reason = "명확한 패턴이 없어 기본값(답변 피드백)으로 처리"
    
    return {
        "query_type": query_type,
        "keywords": keywords,
        "reason": reason
    }

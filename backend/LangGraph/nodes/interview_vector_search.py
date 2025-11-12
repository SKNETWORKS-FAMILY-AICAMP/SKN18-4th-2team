# interview_vector_search node이름 다음에 오는 노드로
# vectorDB에서 코사인 유사도가 높은 chunck 추출 -> top_K =5
# retrieve_chunk.py를 그대로 사용해도 될거 같은지 판단 필요
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from models import get_embedding_model
from initstate import GraphState
from InterviewPGVector import InterviewPGVector
from utils import make_conn_str

def _build_metadata_filter(keywords: list) -> dict:
    """키워드를 occupation과 question_intent 메타데이터에 매핑하여 SQL 필터 생성
    
    매칭되는 키워드가 없으면 빈 dict 반환 -> VectorDB 검색으로 폴백
    
    Args:
        keywords: 추출된 키워드 리스트
    
    Returns:
        metadata 필터 dictionary (비어있으면 필터링 불가)
    """
    if not keywords:
        return {}
    
    # occupation (7개) 매핑
    OCCUPATION_MAPPING = {
        'ARD': ['예술', '디자인', 'UI', 'UX', '창의', '그래픽'],
        'BM': ['비즈니스', '경영', '기획', '전략', '마케팅', '영업', 'PM', 'PO', '프로젝트 매니저', '프로덕트 매니저'],
        'ICT': ['개발자', '개발', '프로그래밍', '코딩', '프론트엔드', '백엔드', '풀스택', 
                '소프트웨어', 'Java', 'Python', 'JavaScript', 'C++', 'React', 'Vue', 'Spring', 'Django', 'Flask',
                'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', '클라우드', '데브옥스'],
        'MM': ['재무', '회계', '재무관리', '회계사', '세무', '예산', '재정'],
        'PS': ['생산', '제조', '생산관리', '품질관리', '공장', '공정', '생산성'],
        'RND': ['연구', '개발', '연구개발', 'R&D', '연구원', '기술개발', '신기술', '특허',
                'AI', '머신러닝', '데이터', '데이터분석', '데이터 사이언스'],
        'SM': ['영업', '판매', '마케팅', '세일즈', '영업관리', '고객', '세일즈 마케팅']
    }
    
    # question_intent (16개) 매핑 - v3 우선순위 반영
    QUESTION_INTENT_MAPPING = {
        # 1) motivation_fit - 목표/지원동기/선호/희망부서
        'motivation_fit': [
            '목표', '지원동기', '지원', '동기', '포부', '우리회사', '적합', 
            '우선순위', '중점적', '선호', '희망부서', '희망', '부서', 
            '가고싶은', '회사', '선호부서'
        ],
        
        # 2) self_reflection - 후회/장단점/자기소개/자신있는
        'self_reflection': [
            '후회', '강점', '약점', '장점', '단점', '자기소개', '자기', 
            '스스로', '자신있는', '수준', '숙련', '레벨', '대표적', 
            '프로젝트', '반성', '성찰', '학습', '성장'
        ],
        
        # 3) criteria_evaluation - 중요하게 생각/기준/평가척도
        'criteria_evaluation': [
            '기준', '평가척도', '평가', '판단기준', '판단', '선정기준', 
            '품질기준', '품질', '중요하게', '생각', '기준점', '측정'
        ],
        
        # 4) stakeholder_comm - 협업/갈등/커뮤니케이션/조율
        'stakeholder_comm': [
            '협업', '갈등', '소통', '설듵', '보고', '피드백', '커뮤니케이션', 
            '이해관계자', '조율', '협력', '팀워크', '팀'
        ],
        
        # 5) behavioral_star - 경험/사례/극복/성과/결과
        'behavioral_star': [
            '경험', '사례', '극볹', '성과', '결과', '해결', '대응', 
            'STAR', 'star', '경험담', '상황', '행동', '어떻게해결', '어떻게대응'
        ],
        
        # 6) procedure_method - 어떻게/방법/절차/프로세스
        'procedure_method': [
            '어떻게', '방법', '방법론', '절차', '프로세스', '순서', 
            '단계', '지침', '절차서', 'how to', 'howto'
        ],
        
        # 7) mechanism_reason - 왜/이유/원인/소감/원리
        'mechanism_reason': [
            '왜', '이유', '원인', '배경', '원리', '생각', '소감', '인과', 
            '메커니즘', '작동원리', '개념', '동작',
            'OOP', '디자인패턴', '알고리즘', '자료구조', '네트워크', 
            '데이터베이스', '기술', '기술면접'
        ],
        
        # 8) compare_tradeoff - 비교/장단점/vs/trade-off
        'compare_tradeoff': [
            '비교', '장단점', '대안', '차이', 'vs', 'VS', 'trade-off', 'tradeoff', 
            '트레이드오프', '선택', '중에', '어느', '더'
        ],
        
        # 9) evidence_metric - 지표/수치/실험/검증/AUC/F1
        'evidence_metric': [
            '지표', '수치', '근거', '증거', '성능', '정확도', '정밀도', 
            '재현율', 'F1', 'f1', 'AUC', 'auc', '실험', '검증', 'validation', 
            '통계', 'p-value', 'pvalue', '신뢰구간', '성과측정'
        ],
        
        # 10) leadership_ownership - 리더십/오너십/주도/책임
        'leadership_ownership': [
            '리더십', '오너십', '주도', '책임', '권한', '위임', '결정', 
            '주도적', '주인의식', '이끌어'
        ],
        
        # 11) creativity_ideation - 창의/개선/아이디어/정책제안
        'creativity_ideation': [
            '새로운', '혁신', '개선', '아이디어', '창의', '창의성', '창의력',
            '브레인스토밍', '개선방안', '정책제안', '제안', '창조', '발상'
        ],
        
        # 12) root_cause - 원인분석/재발방지/디버그/트러블슈팅
        'root_cause': [
            '원인분석', '근본원인', '재발방지', '재발', '트러블슈팅', 
            '디버그', '문제해결', '해결', '분석'
        ],
        
        # 13) ethics_compliance - 윤리/준법/IRB/GDPR/개인정보
        'ethics_compliance': [
            '윤리', '준법', '컴플라이언스', 'IRB', 'irb', 'GDPR', 'gdpr', 
            'HIPAA', 'hipaa', '개인정보', '보안정책', '보안', '법규', '규정', '준수'
        ],
        
        # 14) application_transfer - 적용/현장/전이/실무적용/use case
        'application_transfer': [
            '적용', '현장', '전이', '다른상황', '다른산업', 'use case', 'usecase', 
            '실무적용', '실무', '활용', '응용', '확장'
        ],
        
        # 15) estimation_planning - 대략/예상/일정/계획/리소스계획
        'estimation_planning': [
            '대략', '얼마나', '예상', '추정', '일정', '계획', '납기', 
            '스케줄', '리소스계획', '목표기간', '기획', '예측'
        ],
        
        # 16) cost_resource - 비용/ROI/예산/원가/효율/가성비
        'cost_resource': [
            '비용', 'ROI', 'roi', '예산', '원가', '인력', '장비', '효율', 
            '투입대비', '가성비', '비용효율', '자원', '자원관리'
        ]
    }
    
    # 키워드에서 occupation과 question_intent 분리
    matched_occupation = None
    matched_intent = None
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # occupation 매칭 체크
        if not matched_occupation:
            for occ_code, occ_keywords in OCCUPATION_MAPPING.items():
                for occ_kw in occ_keywords:
                    if keyword == occ_kw or keyword_lower == occ_kw.lower():
                        matched_occupation = occ_code
                        break
                if matched_occupation:
                    break
        
        # question_intent 매칭 체크
        if not matched_intent:
            for intent_code, intent_keywords in QUESTION_INTENT_MAPPING.items():
                for intent_kw in intent_keywords:
                    if keyword == intent_kw or keyword_lower == intent_kw.lower():
                        matched_intent = intent_code
                        break
                if matched_intent:
                    break
        
        # 둘 다 찾았으면 조기 종료
        if matched_occupation and matched_intent:
            break
    
    # 필터 생성: occupation 또는 question_intent 중 하나라도 매칭되면 필터링
    filter_dict = {}
    
    if matched_occupation:
        filter_dict["occupation"] = matched_occupation
    
    if matched_intent:
        filter_dict["question_intent"] = matched_intent
    
    # 매칭되는 키워드가 없으면 빈 dict 반환 -> VectorDB로 폴백
    return filter_dict


def interview_vector_search_node(state: GraphState) -> GraphState:
    """면접 관련 질문과 유사한 chunk를 VectorDB에서 검색하는 노드
    
    코사인 유사도가 높은 chunk를 top_k=5개 추출하여 state에 저장
    
    query_type에 따라 다른 검색 방식 사용:
    - question_recommendation: SQL 필터링 + VectorDB 검색
    - answer_feedback: VectorDB 검색만 사용
    """
    embed = get_embedding_model()
    # 면접 데이터용 InterviewPGVector 사용
    vectorstore = InterviewPGVector(
        conn_str=make_conn_str(), 
        embedding_fn=embed
    )
    
    chunk_lst = list()
    question = state.get("question", "")
    query_type = state.get("interview_query_type", "answer_feedback")
    keywords = state.get("interview_keywords", [])
    
    # query_type에 따라 분기 처리
    if query_type == "question_recommendation" and keywords:
        # 질문 추천: SQL 필터링을 사용하여 검색
        # keywords를 metadata 필터로 사용
        filter_metadata = _build_metadata_filter(keywords)
        
        if filter_metadata:
            # metadata 필터링과 함께 검색
            results = vectorstore.similarity_search(
                query=question,
                k=5,
                filter=filter_metadata
            )
            # similarity_search는 score를 반환하지 않으므로 별도 처리
            for doc in results:
                chunk_lst.append({
                    "content": doc.page_content,
                    "score": 0.0,  # 필터링된 결과는 score를 별도로 계산하지 않음
                    "metadata": {**(doc.metadata or {})}
                })
        else:
            # 키워드가 있지만 필터 생성 실패 시 기본 검색
            results = vectorstore.similarity_search_with_score(question, k=5)
            for doc, score in results:
                chunk_lst.append({
                    "content": doc.page_content,
                    "score": float(score),
                    "metadata": {**(doc.metadata or {})}
                })
    else:
        # 답변 피드백: 일반 VectorDB 검색
        results = vectorstore.similarity_search_with_score(question, k=5)
        
        for doc, score in results:
            chunk_lst.append({
                "content": doc.page_content,
                "score": float(score),
                "metadata": {**(doc.metadata or {})}
            })
    
    state["chunks"] = chunk_lst
    
    return state



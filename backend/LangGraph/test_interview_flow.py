"""면접 플로우 테스트 스크립트

classify → interview_query_classify → interview_vector_search → interview_eval → interview_generation → END
"""
import sys
from pathlib import Path

# LangGraph 디렉토리와 backend 디렉토리를 모두 path에 추가
langraph_dir = Path(__file__).resolve().parent
backend_dir = langraph_dir.parent
sys.path.insert(0, str(langraph_dir))
sys.path.insert(0, str(backend_dir))

from graph import create_graph_flow
from initstate import GraphState
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def test_interview_flow():
    """면접 플로우 테스트"""
    
    # 그래프 생성
    print("=" * 80)
    print("그래프 생성 중...")
    print("=" * 80)
    graph = create_graph_flow()
    
    # 테스트 케이스 1: 질문 추천
    test_case_1 = {
        "user": "취업 준비생, 소프트웨어 개발자 지망",
        "question": "백엔드 개발자 면접에서 자주 나오는 질문들을 추천해 주세요",
        "category": "",
        "generate_question": "",
        "chunks": [],
        "final_chunks": [],
        "answer": "",
        "final_answer": "",
        "interview_query_type": "",
        "interview_keywords": [],
        "classification_reason": "",
        "eval_score": 0.0,
        "eval_reason": ""
    }
    
    # 테스트 케이스 2: 답변 피드백
    test_case_2 = {
        "user": "취업 준비생, 프론트엔드 개발자 지망",
        "question": "자기소개를 해달라는 면접 질문에 어떻게 대답하면 좋을까요?",
        "category": "",
        "generate_question": "",
        "chunks": [],
        "final_chunks": [],
        "answer": "",
        "final_answer": "",
        "interview_query_type": "",
        "interview_keywords": [],
        "classification_reason": "",
        "eval_score": 0.0,
        "eval_reason": ""
    }
    
    # 테스트 실행
    test_cases = [
        ("질문 추천", test_case_1),
        ("답변 피드백", test_case_2)
    ]
    
    for test_name, test_input in test_cases:
        print("\n" + "=" * 80)
        print(f"테스트: {test_name}")
        print("=" * 80)
        print(f"사용자: {test_input['user']}")
        print(f"질문: {test_input['question']}")
        print("\n실행 중...\n")
        
        try:
            # 그래프 실행
            result = graph.invoke(test_input)
            
            print("-" * 80)
            print("결과:")
            print("-" * 80)
            print(f"카테고리: {result.get('category', 'N/A')}")
            print(f"면접 질문 유형: {result.get('interview_query_type', 'N/A')}")
            print(f"추출된 키워드: {result.get('interview_keywords', [])}")
            print(f"분류 이유: {result.get('classification_reason', 'N/A')}")
            print(f"\n검색된 청크 수: {len(result.get('chunks', []))}")
            print(f"최종 선택된 청크 수: {len(result.get('final_chunks', []))}")
            
            if result.get('final_chunks'):
                print("\n최종 청크 평가:")
                for i, chunk in enumerate(result['final_chunks'][:3], 1):
                    metadata = chunk.get('metadata', {})
                    print(f"\n[청크 {i}]")
                    print(f"  평가 점수: {chunk.get('eval_score', 'N/A')}")
                    print(f"  평가 이유: {chunk.get('eval_reason', 'N/A')[:100]}...")
                    print(f"\n  메타데이터:")
                    print(f"    - doc_id: {metadata.get('doc_id', 'N/A')}")
                    print(f"    - occupation: {metadata.get('occupation', 'N/A')}")
                    print(f"    - question_intent: {metadata.get('question_intent', 'N/A')}")
                    print(f"    - gender: {metadata.get('gender', 'N/A')}")
                    print(f"    - age_range: {metadata.get('age_range', 'N/A')}")
                    print(f"    - experience: {metadata.get('experience', 'N/A')}")
                    print(f"\n  내용 미리보기: {chunk.get('content', '')[:200]}...")
            
            print("\n" + "-" * 80)
            print("최종 답변:")
            print("-" * 80)
            print(result.get('final_answer', 'N/A'))
            
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()


def test_interview_flow_step_by_step():
    """면접 플로우 단계별 테스트 (디버깅용)"""
    
    print("=" * 80)
    print("단계별 테스트 시작")
    print("=" * 80)
    
    graph = create_graph_flow()
    
    test_input = {
        "user": "취업 준비생, AI 엔지니어 지망",
        "question": "머신러닝 면접에서 자주 나오는 질문을 추천해 주세요",
        "category": "",
        "generate_question": "",
        "chunks": [],
        "final_chunks": [],
        "answer": "",
        "final_answer": "",
        "interview_query_type": "",
        "interview_keywords": [],
        "classification_reason": "",
        "eval_score": 0.0,
        "eval_reason": ""
    }
    
    try:
        # 스트리밍으로 각 단계 출력
        for step_output in graph.stream(test_input):
            node_name = list(step_output.keys())[0]
            node_result = step_output[node_name]
            
            print("\n" + "=" * 80)
            print(f"노드: {node_name}")
            print("=" * 80)
            
            if node_name == "classify":
                print(f"카테고리: {node_result.get('category', 'N/A')}")
            
            elif node_name == "interview_query_classify":
                print(f"질문 유형: {node_result.get('interview_query_type', 'N/A')}")
                print(f"키워드: {node_result.get('interview_keywords', [])}")
                print(f"분류 이유: {node_result.get('classification_reason', 'N/A')}")
            
            elif node_name == "interview_vector_search":
                print(f"검색된 청크 수: {len(node_result.get('chunks', []))}")
                if node_result.get('chunks'):
                    print(f"첫 번째 청크 점수: {node_result['chunks'][0].get('score', 'N/A')}")
            
            elif node_name == "interview_eval":
                print(f"평가된 청크 수: {len(node_result.get('final_chunks', []))}")
                for i, chunk in enumerate(node_result.get('final_chunks', [])[:3], 1):
                    metadata = chunk.get('metadata', {})
                    print(f"\n청크 {i}:")
                    print(f"  점수: {chunk.get('eval_score', 'N/A')}")
                    print(f"  occupation: {metadata.get('occupation', 'N/A')}")
                    print(f"  question_intent: {metadata.get('question_intent', 'N/A')}")
            
            elif node_name == "interview_generation":
                print("최종 답변 생성 완료")
                print(f"답변 길이: {len(node_result.get('final_answer', ''))} 자")
    
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="면접 플로우 테스트")
    parser.add_argument(
        "--mode",
        choices=["normal", "step"],
        default="normal",
        help="테스트 모드: normal(일반) 또는 step(단계별)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "step":
        test_interview_flow_step_by_step()
    else:
        test_interview_flow()

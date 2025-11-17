# 1. LLM 기반 질문과, 추출된 chunk의 맥락상 유사도를 평가하는 interview_eval_agent를 불어오는 노드
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from initstate import GraphState
from agent.interview_eval_agent import evaluate_interview_chunk_relevance


def interview_eval_node(state: GraphState) -> GraphState:
    """면접 질문과 chunk들의 맥락적 유사도를 평가하는 노드
    
    interview_eval_agent를 사용하여 각 chunk를 평가하고,
    eval_score 기준으로 정렬하여 상위 3개를 final_chunks에 저장
    """
    evaluated_chunks = []
    chunks = state.get("chunks", [])
    question = state.get("question", "")
    
    for chunk in chunks:
        content = chunk.get("content", "")
        
        # interview_eval_agent를 호출하여 평가
        eval_result = evaluate_interview_chunk_relevance(question, content)
        
        # chunk에 평가 결과 추가
        chunk_with_eval = {
            **chunk,
            "eval_score": eval_result["score"],
            "eval_reason": eval_result["reason"],
        }
        evaluated_chunks.append(chunk_with_eval)
    
    # eval_score 기준으로 내림차순 정렬
    sorted_chunks = sorted(
        evaluated_chunks, 
        key=lambda ch: ch.get("eval_score", 0.0), 
        reverse=True
    )
    
    # 최소 점수 임계값 적용 (0.5 이상만 사용)
    MIN_RELEVANCE_SCORE = 0.4
    filtered_chunks = [
        chunk for chunk in sorted_chunks 
        if chunk.get("eval_score", 0.0) >= MIN_RELEVANCE_SCORE
    ]
    
    # 상위 3개 선택 (필터링 후)
    state["final_chunks"] = filtered_chunks[:3]
    
    # 디버그: 필터링 결과 출력
    # print(f"[EVAL] Total chunks: {len(evaluated_chunks)}, Filtered (>={MIN_RELEVANCE_SCORE}): {len(filtered_chunks)}, Final: {len(state['final_chunks'])}")
    # for i, chunk in enumerate(state["final_chunks"]):
    #     print(f"[EVAL] Chunk {i+1}: Score={chunk.get('eval_score'):.2f}, Reason={chunk.get('eval_reason')[:50]}...")
    
    return state

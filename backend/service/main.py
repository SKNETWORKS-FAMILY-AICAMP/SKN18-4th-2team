from pathlib import Path
import sys
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))
from LangGraph.graph import create_collage_graph_flow


def main():
    app = create_collage_graph_flow()
    
    answer = app.invoke({
        "user": "고등학생",
        "question": "AI 관련 학과 진로가 궁금해"
    })
    
    print("\n=== 최종 답변 ===")
    print(answer["final_answer"])
    print("\n=== 평가 결과 ===")
    print(answer.get("evaluation", {}))

if __name__ == "__main__":
    load_dotenv()
    main()
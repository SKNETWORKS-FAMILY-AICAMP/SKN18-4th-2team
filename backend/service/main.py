from pathlib import Path
import sys
from dotenv import load_dotenv

# 상위 폴더를 import 경로에 추가
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.LangGraph.graph import create_graph_flow


def main():
    load_dotenv()
    app = create_graph_flow()
    print("🤖 LangGraph 챗봇 활성화 완료!")
    print("종료하려면 'exit', 'quit', '종료' 입력.\n")

    while True:
        question = input("🧠 질문: ").strip()
        if question.lower() in ["exit", "quit", "종료"]:
            print("👋 챗봇을 종료합니다.")
            break

        # 사용자 state 입력값 구성
        state = {
            "user": "고등학생",
            "question": question
        }

        # 그래프 실행
        answer = app.invoke(state)

        print("\n=== 💬 최종 답변 ===")
        print(answer.get("final_answer") or answer)
        print("\n=== 📊 평가 결과 ===")
        print(answer.get("evaluation", {}))
        print("\n────────────────────────────\n")


if __name__ == "__main__":
    main()

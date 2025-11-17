from pathlib import Path
import sys
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))
from LangGraph.graph import create_graph_flow


def main():
    app = create_graph_flow()
    
    answer = app.invoke({"user": "취업준비생", "question": "개발회사에서 면접을 보는데 리더십 관련 질문 알려줘."})


if __name__ == "__main__":
    load_dotenv()
    main()
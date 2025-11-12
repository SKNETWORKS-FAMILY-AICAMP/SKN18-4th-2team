from pathlib import Path
import sys
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))
from LangGraph.graph import create_collage_graph_flow


def main():
    app = create_collage_graph_flow()
    
    answer = app.invoke({"user": "고등학생", "question": ""})

    print(answer["answer"])

if __name__ == "__main__":
    load_dotenv()
    main()
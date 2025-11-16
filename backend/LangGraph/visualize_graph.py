from importlib import import_module
from pathlib import Path
import sys

from dotenv import load_dotenv

langraph_dir = Path(__file__).resolve().parent
backend_dir = langraph_dir.parent
sys.path.insert(0, str(backend_dir))  # allow `LangGraph` namespace imports

graph_module = import_module("LangGraph.graph")
create_graph_flow = graph_module.create_graph_flow  # type: ignore[attr-defined]

load_dotenv()

if __name__ == "__main__":
    print("=" * 60)
    print("대학, 진로 상담 챗봇")
    print("=" * 60)

    try:
        app = create_graph_flow()
        print("[완료] 그래프 빌드 완료!")

        print("\n=== 그래프 구조 (Mermaid) ===")
        mermaid_output = app.get_graph().draw_mermaid()
        unique_lines = []
        seen = set()
        for line in mermaid_output.splitlines():
            if line not in seen:
                unique_lines.append(line)
                seen.add(line)
        print("\n".join(unique_lines))

        try:
            print("\n그래프를 PNG로 저장 중...")
            img = app.get_graph().draw_mermaid_png()
            output_path = Path(__file__).parent / "graph_structure.png"
            output_path.write_bytes(img)
            print(f"[완료] {output_path} 파일로 저장 완료!")
        except Exception as png_error:
            print(f"PNG 저장 실패 (무시): {png_error}")
    except Exception as build_error:
        print(f"[실패] 그래프 빌드 실패: {build_error}")
        raise

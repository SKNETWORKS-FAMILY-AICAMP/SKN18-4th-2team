from models import get_embedding_model
from initstate import GraphState
from CustomPGvector import CustomPGVector
from utils import make_conn_str


def retrieve_chunks_node(state: GraphState) -> GraphState:
    """질문과 유사한 chunk 가져오는 노드"""
    embed = get_embedding_model()
    vectorstore = CustomPGVector(conn_str=make_conn_str(), embedding_fn=embed)
    chunk_lst = list()
    question = state["question"]
    results = vectorstore.similarity_search_with_score(question, k=5)
    for doc, score in results:
        chunk_lst.append({"content": doc.page_content, "score": float(score), "metadata": {**(doc.metadata or {})}})
    state["chunks"] = chunk_lst
    return state
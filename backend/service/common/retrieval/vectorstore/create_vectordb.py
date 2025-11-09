from pathlib import Path

from dotenv import load_dotenv

from backend.service.common.model import set_embedding_model
from backend.service.common.retrieval.vectorstore.vectordb.connect_db import connect_DB
from backend.service.common.retrieval.vectorstore.vectordb.data_loader import (
    load_chunk_rows,
    load_university_rows,
)
from backend.service.common.retrieval.vectorstore.vectordb.pgvector import (
    upsert_embeddings,
    upsert_universities,
)
from backend.service.common.retrieval.vectorstore.vectordb.splitter import (
    split_chunk_rows,
)

SERVICE_DIR = Path(__file__).resolve().parents[3]
PROJECT_ROOT = SERVICE_DIR.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BATCH_SIZE = 32
CHUNK_SIZE = 220
CHUNK_OVERLAP = 50


def create_major_vectordb() -> None:
    """Full ingestion pipeline for major vectors + supporting university table."""
    db = connect_DB()
    embeddings = set_embedding_model()
    chunk_rows = load_chunk_rows()
    chunk_rows = split_chunk_rows(
        chunk_rows, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    upsert_embeddings(db, embeddings, chunk_rows, batch_size=BATCH_SIZE)
    univ_rows = load_university_rows()
    upsert_universities(db, univ_rows)


if __name__ == "__main__":
    create_major_vectordb()

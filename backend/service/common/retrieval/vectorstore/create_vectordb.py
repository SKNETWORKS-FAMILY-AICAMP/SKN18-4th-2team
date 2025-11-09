import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List

from dotenv import load_dotenv
import psycopg2
from psycopg2 import extensions
from psycopg2.extras import Json
from pgvector.psycopg2 import register_vector
from tqdm import tqdm

from ...model import set_embedding_model

BACKEND_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BACKEND_DIR.parent / ".env")
CSV_PATH = BACKEND_DIR / "database" / "college" / "majors_with_chunks.csv"
BATCH_SIZE = 32


def load_chunks_from_csv(csv_path: Path = CSV_PATH) -> List[Dict[str, str]]:
    """Load flattened major rows (metadata + chunk field) from the CSV export."""
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found. 먼저 export_to_csv.py를 실행하세요.")

    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _env(key: str) -> str:
    """Return the environment variable for the given key."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"{key} is not set in the environment.")
    return value


def _get_connection() -> extensions.connection:
    conn = psycopg2.connect(
        host=_env("POSTGRES_HOST"),
        port=_env("POSTGRES_PORT"),
        dbname=_env("POSTGRES_DB"),
        user=_env("POSTGRES_USER"),
        password=_env("POSTGRES_PASSWORD"),
    )
    register_vector(conn)
    return conn


UPSERT_SQL = """
INSERT INTO major_vector_chunks (
    major_seq,
    major,
    salary,
    employment,
    job,
    qualifications,
    chunk_field,
    chunk_text,
    embedding,
    metadata
)
VALUES (
    %(major_seq)s,
    %(major)s,
    %(salary)s,
    %(employment)s,
    %(job)s,
    %(qualifications)s,
    %(chunk_field)s,
    %(chunk_text)s,
    %(embedding)s,
    %(metadata)s
)
ON CONFLICT (major_seq, chunk_field)
DO UPDATE SET
    salary = EXCLUDED.salary,
    employment = EXCLUDED.employment,
    job = EXCLUDED.job,
    qualifications = EXCLUDED.qualifications,
    chunk_text = EXCLUDED.chunk_text,
    embedding = EXCLUDED.embedding,
    metadata = EXCLUDED.metadata;
"""


def upsert_embeddings(records: Iterable[Dict[str, str]], batch_size: int = BATCH_SIZE) -> None:
    """
    Generate embeddings from CSV rows and insert/update them in pgvector.

    Args:
        records: Iterable rows loaded via `load_chunks_from_csv`.
        batch_size: Number of rows to embed per API call.
    """

    rows = list(records)
    if not rows:
        print("No records to ingest.")
        return

    embedder = set_embedding_model()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            for start in tqdm(range(0, len(rows), batch_size), desc="Embedding batches"):
                batch = rows[start : start + batch_size]
                vectors = embedder.embed_documents([row["chunk_text"] for row in batch])

                payload = []
                for row, vector in zip(batch, vectors, strict=True):
                    metadata = {
                        "majorSeq": row.get("majorSeq"),
                        "chunkField": row.get("chunk_field"),
                    }
                    payload.append(
                        {
                            "major_seq": row.get("majorSeq"),
                            "major": row.get("major"),
                            "salary": row.get("salary"),
                            "employment": row.get("employment"),
                            "job": row.get("job"),
                            "qualifications": row.get("qualifications"),
                            "chunk_field": row.get("chunk_field"),
                            "chunk_text": row.get("chunk_text"),
                            "embedding": vector,
                            "metadata": Json(metadata),
                        }
                    )

                cur.executemany(UPSERT_SQL, payload)
                conn.commit()

    print(f"Upserted {len(rows)} chunk rows into pgvector.")


if __name__ == "__main__":
    data = load_chunks_from_csv()
    upsert_embeddings(data)

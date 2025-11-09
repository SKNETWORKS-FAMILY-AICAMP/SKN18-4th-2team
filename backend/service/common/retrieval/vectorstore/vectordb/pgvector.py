from typing import Any, Dict, Iterable, List

from psycopg2.extras import Json
from tqdm import tqdm

from .data_loader import iter_batches

UPSERT_SQL = """
INSERT INTO major_vector_chunks (
    major_seq,
    major,
    salary,
    employment,
    job,
    qualifications,
    chunk_field,
    chunk_index,
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
    %(chunk_index)s,
    %(chunk_text)s,
    %(embedding)s,
    %(metadata)s
)
ON CONFLICT (major_seq, chunk_field, chunk_index)
DO UPDATE SET
    salary = EXCLUDED.salary,
    employment = EXCLUDED.employment,
    job = EXCLUDED.job,
    qualifications = EXCLUDED.qualifications,
    chunk_index = EXCLUDED.chunk_index,
    chunk_text = EXCLUDED.chunk_text,
    embedding = EXCLUDED.embedding,
    metadata = EXCLUDED.metadata;
"""

UNIV_UPSERT_SQL = """
INSERT INTO major_universities (
    major_seq,
    school_name,
    major_name
)
VALUES (
    %(major_seq)s,
    %(school_name)s,
    %(major_name)s
)
ON CONFLICT (major_seq, school_name, major_name) DO NOTHING;
"""


def upsert_embeddings(db, embedder, rows: Iterable[Dict[str, Any]], batch_size: int = 32) -> None:
    """Generate embeddings for each chunk row and upsert into pgvector."""
    rows = list(rows)
    if not rows:
        print("No chunk rows to ingest.")
        return

    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            for batch in tqdm(iter_batches(rows, batch_size), desc="Embedding batches"):
                vectors = embedder.embed_documents([row.get("chunk_text", "") for row in batch])
                payload: List[Dict[str, Any]] = []
                for row, vector in zip(batch, vectors, strict=True):
                    metadata = {
                        "majorSeq": row.get("majorSeq"),
                        "chunkField": row.get("chunk_field"),
                        "chunkIndex": row.get("chunk_index", 0),
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
                            "chunk_index": int(row.get("chunk_index", 0)),
                            "chunk_text": row.get("chunk_text"),
                            "embedding": vector,
                            "metadata": Json(metadata),
                        }
                    )

                cur.executemany(UPSERT_SQL, payload)
                conn.commit()
    finally:
        db.put_connection(conn)

    print(f"Upserted {len(rows)} chunk rows into pgvector.")


def upsert_universities(db, rows: Iterable[Dict[str, Any]]) -> None:
    """Insert university rows for each major (deduplicated via ON CONFLICT)."""
    rows = list(rows)
    if not rows:
        print("No university records to ingest.")
        return

    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany(
                UNIV_UPSERT_SQL,
                [
                    {
                        "major_seq": row.get("majorSeq"),
                        "school_name": row.get("schoolName"),
                        "major_name": row.get("majorName"),
                    }
                    for row in rows
                ],
            )
        conn.commit()
    finally:
        db.put_connection(conn)

    print(f"Upserted {len(rows)} university rows.")

from typing import Any, Dict, List, Optional, Sequence, Tuple
import json

from psycopg2.extras import Json
import psycopg2

from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document

class Singleton(type(VectorStore)):
    _instances: Dict[type, VectorStore] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class CustomPGVector(VectorStore, metaclass=Singleton):
    DEFAULT_TABLE = "college.college_vector_db"
    _CONTENT_FALLBACK_KEYS: Sequence[str] = (
        "summary",
        "interest",
        "property",
        "job",
        "qualifications",
    )

    def __init__(self, conn_str, embedding_fn, table: str | None = None):
        self.conn_str = conn_str
        self.conn = psycopg2.connect(self.conn_str)
        self.embedding_fn = embedding_fn
        self.table = table or self.DEFAULT_TABLE

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding_fn,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        conn_str: str | None = None,
        table: str | None = None,
        **kwargs,
    ):
        store = cls(conn_str=conn_str, embedding_fn=embedding_fn, table=table)
        store.add_texts(texts, metadatas=metadatas)
        return store

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        metadatas = metadatas or [{} for _ in texts]
        embeddings = self.embedding_fn.embed_documents(texts)

        insert_sql = f"""
            INSERT INTO {self.table} (
                major_seq,
                major,
                salary,
                employment,
                job,
                qualifications,
                universities,
                embedding,
                metadata
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        with self.conn.cursor() as cur:
            for text, emb, meta in zip(texts, embeddings, metadatas):
                payload = self._prepare_insert_payload(text, emb, meta)
                cur.execute(insert_sql, payload)
        self.conn.commit()

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        query_emb = self.embedding_fn.embed_query(query)
        params: List[Any] = []

        sql_query_template = f"""
            SELECT
                major_seq,
                major,
                salary,
                employment,
                job,
                qualifications,
                universities,
                metadata
            FROM {self.table}
        """

        where_clauses: List[str] = []
        if filter:
            filter_json = json.dumps(filter)
            where_clauses.append("metadata @> %s::jsonb")
            params.append(filter_json)

        if where_clauses:
            sql_query_template += " WHERE " + " AND ".join(where_clauses)

        sql_query_template += """
            ORDER BY embedding <-> %s::vector
            LIMIT %s
        """
        params.append(query_emb)
        params.append(k)

        with self.conn.cursor() as cur:
            cur.execute(sql_query_template, tuple(params))
            rows = cur.fetchall()

        return self.__hydrate_documents(rows)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
    ) -> List[Tuple[Document, float]]:
        query_emb = self.embedding_fn.embed_query(query)

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    major_seq,
                    major,
                    salary,
                    employment,
                    job,
                    qualifications,
                    universities,
                    metadata,
                    (embedding <-> %s::vector) AS score
                FROM {self.table}
                ORDER BY score
                LIMIT %s
                """,
                (query_emb, k),
            )
            rows = cur.fetchall()

        documents = []
        for row in rows:
            *doc_fields, score = row
            doc = self.__hydrate_row(tuple(doc_fields))
            documents.append((doc, float(score)))
        return self.__dedupe_with_score(documents)

    @staticmethod
    def __dedupe_with_score(items: List[Tuple[Document, float]]) -> List[Tuple[Document, float]]:
        seen_contents = set()
        unique: List[Tuple[Document, float]] = []
        for doc, score in items:
            content = doc.page_content
            if content in seen_contents:
                continue
            seen_contents.add(content)
            unique.append((doc, score))
        return unique

    def __hydrate_documents(self, rows: List[Tuple[Any, ...]]) -> List[Document]:
        unique_contents = set()
        documents: List[Document] = []
        for row in rows:
            doc = self.__hydrate_row(row)
            if doc.page_content in unique_contents:
                continue
            unique_contents.add(doc.page_content)
            documents.append(doc)
        return documents

    def __hydrate_row(self, row: Tuple[Any, ...]) -> Document:
        (
            major_seq,
            major,
            salary,
            employment,
            job,
            qualifications,
            universities,
            metadata,
        ) = row

        metadata_dict = metadata or {}
        if not isinstance(metadata_dict, dict):
            metadata_dict = {}

        doc_metadata: Dict[str, Any] = {
            "major_seq": major_seq,
            "major": major,
            "salary": salary,
            "employment": employment,
            "job": job,
            "qualifications": qualifications,
            "universities": universities,
        }
        doc_metadata.update(metadata_dict)

        page_content = metadata_dict.get("page_content") or self.__compose_content(doc_metadata)
        return Document(page_content=page_content, metadata=doc_metadata)

    def __compose_content(self, metadata: Dict[str, Any]) -> str:
        parts: List[str] = []
        for key in self._CONTENT_FALLBACK_KEYS:
            value = metadata.get(key)
            if value:
                parts.append(f"{key}: {value}")
        return " | ".join(parts)

    def _prepare_insert_payload(self, text: str, embedding: List[float], metadata: Dict[str, Any]) -> Tuple[Any, ...]:
        meta = metadata or {}
        lookup = lambda *keys: next((meta.get(k) for k in keys if meta.get(k)), None)

        major_seq = lookup("major_seq", "majorSeq")
        major = lookup("major", "majorName")
        if not major_seq or not major:
            raise ValueError("Both 'majorSeq' and 'major' metadata fields are required.")

        def _sanitize(value: Any) -> Optional[str]:
            if value is None or value == "":
                return None
            return str(value)

        salary = _sanitize(lookup("salary"))
        employment = _sanitize(lookup("employment"))
        job = _sanitize(lookup("job"))
        qualifications = _sanitize(lookup("qualifications"))
        universities = _sanitize(lookup("universities"))

        metadata_payload = dict(meta)
        metadata_payload.setdefault("majorSeq", major_seq)
        metadata_payload.setdefault("major", major)
        metadata_payload.setdefault("page_content", text)

        return (
            str(major_seq),
            str(major),
            salary,
            employment,
            job,
            qualifications,
            universities,
            embedding,
            Json(metadata_payload),
        )

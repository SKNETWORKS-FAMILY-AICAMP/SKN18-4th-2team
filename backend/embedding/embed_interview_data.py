#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
embed_data.py  (patched)
- Korean-friendly sentence boundary chunking
- Length-aware chunking rules with overlap
- Answer embedding = mean of per-chunk embeddings
- Keeps DB schema and external search code unchanged
"""

import os
import re
import sys
import time
from typing import List, Tuple, Dict

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from tqdm import tqdm
from openai import OpenAI
import tiktoken

# =============================================================================
# Config
# =============================================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "3072"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "skn4th_db"),
    "user": os.getenv("DB_USER", "skn4th"),
    "password": os.getenv("DB_PASSWORD", "skn4th1234"),
}

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "0.2"))  # seconds

# Chunking thresholds (can be moved to .env if needed)
CHUNK_ONE_MAX = int(os.getenv("CHUNK_ONE_MAX", "350"))     # ≤350: single chunk
CHUNK_TWO_MAX = int(os.getenv("CHUNK_TWO_MAX", "600"))     # 351~600: 2 chunks with overlap
OVERLAP_CHARS = int(os.getenv("OVERLAP_CHARS", "30"))      # 20~40 recommended; default 30
LONG_TARGET = int(os.getenv("LONG_TARGET", "350"))         # target length for long answers (≈350)

# =============================================================================
# Sentence split & chunking utilities
# =============================================================================

# Rough Korean-friendly sentence boundary splitter
SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+|(?<=다\.)\s+|(?<=요\.)\s+|(?<=[\u3002\uFF01\uFF1F])\s+')

def split_sentences(text: str) -> List[str]:
    """Split text into sentences with basic Korean-friendly regex."""
    text = re.sub(r'\s+', ' ', text or '').strip()
    if not text:
        return []
    sents = [s.strip() for s in SENT_SPLIT_RE.split(text) if s.strip()]
    return sents

def join_until_len(sents: List[str], start: int, max_len: int) -> Tuple[str, int]:
    """Append sentences starting at `start` until `max_len` approx reached."""
    buf, i = [], start
    length = 0
    while i < len(sents):
        add = ((' ' if buf else '') + sents[i])
        if length + len(add) > max_len and buf:
            break
        buf.append(sents[i])
        length += len(add)
        i += 1
    return ' '.join(buf).strip(), i

def add_overlap(src: str, nxt: str, overlap: int = OVERLAP_CHARS) -> Tuple[str, str]:
    """Prepend tail of `src` to `nxt` for soft continuity in embeddings."""
    if not src or not nxt or overlap <= 0:
        return src, nxt
    left_tail = src[-overlap:]
    if not nxt.startswith(left_tail):
        nxt = (left_tail + nxt).strip()
    return src, nxt

def chunk_answer_by_rule(answer: str) -> List[str]:
    """
    Rules:
    - ≤ CHUNK_ONE_MAX(350): 1 chunk (no overlap)
    - CHUNK_ONE_MAX+1 ~ CHUNK_TWO_MAX(600): 2 chunks with ~30 chars overlap
      * cut at sentence boundary, try to balance lengths
    - > CHUNK_TWO_MAX: up to 3 chunks, each ~LONG_TARGET chars, with overlap
    """
    if not isinstance(answer, str):
        return ['']

    text = re.sub(r'\s+', ' ', answer).strip()
    n = len(text)
    if n <= CHUNK_ONE_MAX:
        return [text]

    sents = split_sentences(text) or [text]
    chunks: List[str] = []

    if CHUNK_ONE_MAX < n <= CHUNK_TWO_MAX:
        half = max(280, min(330, n // 2))  # try to split around mid
        c1, idx = join_until_len(sents, 0, half)
        c2 = ' '.join(sents[idx:]).strip()
        c1, c2 = add_overlap(c1, c2, OVERLAP_CHARS)
        chunks = [c1, c2]
    else:
        # Long case: make up to 3 chunks around LONG_TARGET
        i = 0
        while i < len(sents) and len(chunks) < 3:
            c, i = join_until_len(sents, i, LONG_TARGET)
            if c:
                chunks.append(c)
            else:
                break
        if len(chunks) >= 2:
            chunks[0], chunks[1] = add_overlap(chunks[0], chunks[1], OVERLAP_CHARS)
        if len(chunks) >= 3:
            chunks[1], chunks[2] = add_overlap(chunks[1], chunks[2], OVERLAP_CHARS)

    chunks = [c for c in chunks if c.strip()]
    return chunks or [text]

def avg_vectors(vecs: List[List[float]]) -> List[float]:
    """Compute element-wise mean of vectors (defensive to dim mismatches)."""
    if not vecs:
        return None
    dim = len(vecs[0])
    acc = [0.0] * dim
    count = 0
    for v in vecs:
        if not isinstance(v, list) or len(v) != dim:
            continue
        for i in range(dim):
            acc[i] += v[i]
        count += 1
    if count == 0:
        return None
    return [x / count for x in acc]

# =============================================================================
# Embedder
# =============================================================================

class Embedder:
    def __init__(self, csv_path: str):
        if not OPENAI_API_KEY:
            print("✗ OPENAI_API_KEY not found in environment (.env).")
            sys.exit(1)

        self.csv_path = csv_path
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.conn = None
        self.cur = None

    # ---------- DB ----------
    def connect_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor()
            print("✓ Connected to database")
        except Exception as e:
            print(f"✗ DB connection failed: {e}")
            sys.exit(1)

    def close_db(self):
        try:
            if self.cur: self.cur.close()
            if self.conn: self.conn.close()
            print("✓ Database connection closed")
        except Exception:
            pass

    # ---------- IO ----------
    def load_csv(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.csv_path, encoding="utf-8-sig")
            if not {'question', 'answer'}.issubset(df.columns):
                raise ValueError("CSV must contain 'question' and 'answer' columns.")
            print(f"✓ Loaded {len(df)} rows from {self.csv_path}")
            return df
        except Exception as e:
            print(f"✗ Failed to load CSV: {e}")
            sys.exit(1)

    # ---------- helpers ----------
    @staticmethod
    def create_chunk_id(doc_id: int, suffix: str = "") -> str:
        return f"DOC{int(doc_id):06d}" + (f"_{suffix}" if suffix else "")

    @staticmethod
    def normalize_text(text: str) -> str:
        if not isinstance(text, str):
            return ""
        t = text.lower()
        t = re.sub(r'\s+', ' ', t)
        t = re.sub(r'[^\w\sㄱ-ㅎ가-힣.,!?]', '', t)
        return t.strip()

    def count_tokens(self, text: str) -> int:
        try:
            return len(self.encoding.encode(text or ""))
        except Exception:
            return 0

    def get_embedding(self, text: str) -> List[float]:
        if not text:
            return None
        try:
            resp = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                encoding_format="float",
            )
            return resp.data[0].embedding
        except Exception as e:
            print(f"⚠ Embedding error: {e}")
            return None

    # ---------- Inserts ----------
    def insert_metadata_batch(self, rows: List[tuple]):
        sql = """
        INSERT INTO qa.meta_df (
            chunk_id, doc_id, occupation, gender, age_range, experience,
            answer_intent_category, answer_emotion_expression, answer_emotion_category,
            question_intent, question_text, question_text_norm, answer_text,
            content_combined, tokens_answer, tokens_combined, group_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (chunk_id) DO NOTHING
        """
        try:
            execute_batch(self.cur, sql, rows)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Metadata insert failed: {e}")

    def insert_q_batch(self, rows: List[tuple]):
        sql = """
        INSERT INTO qa.vec_q_index (chunk_id_q, chunk_id, emb_model, emb_dim, embedding)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (chunk_id_q) DO UPDATE SET
            embedding = EXCLUDED.embedding,
            emb_model = EXCLUDED.emb_model,
            emb_dim = EXCLUDED.emb_dim
        """
        try:
            execute_batch(self.cur, sql, rows)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Q-index insert failed: {e}")

    def insert_a_batch(self, rows: List[tuple]):
        # First delete existing entries for these chunk_ids, then insert
        chunk_ids = [row[0] for row in rows]
        try:
            if chunk_ids:
                placeholders = ','.join(['%s'] * len(chunk_ids))
                delete_sql = f"DELETE FROM qa.vec_a_index WHERE chunk_id IN ({placeholders})"
                self.cur.execute(delete_sql, chunk_ids)
            
            insert_sql = """
            INSERT INTO qa.vec_a_index (chunk_id, emb_model, emb_dim, embedding)
            VALUES (%s, %s, %s, %s)
            """
            execute_batch(self.cur, insert_sql, rows)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"A-index insert failed: {e}")

    # ---------- Process ----------
    def process(self):
        df = self.load_csv()
        total = len(df)

        meta_rows, q_rows, a_rows = [], [], []
        ok, err = 0, 0

        print(f"\n🚀 Start embedding ({total} rows)")
        print(f"Model: {EMBEDDING_MODEL} (dim={EMBEDDING_DIMENSION})\n")

        for i, row in tqdm(df.iterrows(), total=total, desc="Embedding"):
            try:
                doc_id = int(row.get('sample_id', i + 1)) if pd.notna(row.get('sample_id')) else (i + 1)
                chunk_id = self.create_chunk_id(doc_id)
                chunk_id_q = self.create_chunk_id(doc_id, "Q")

                question = str(row.get('question', '')).strip()
                answer = str(row.get('answer', '')).strip()

                q_norm = self.normalize_text(question)
                combined = f"Q: {question}\nA: {answer}"
                tok_ans = self.count_tokens(answer)
                tok_all = self.count_tokens(combined)

                # meta
                meta_rows.append((
                    chunk_id,
                    doc_id,
                    str(row.get('occupation', '') or ''),
                    str(row.get('gender', '') or ''),
                    str(row.get('ageRange', '') or ''),
                    str(row.get('experience', '') or ''),
                    str(row.get('answer-intent_category', '') or ''),
                    str(row.get('answer-emotion_expression', '') or ''),
                    str(row.get('answer-emotion_category', '') or ''),
                    str(row.get('question_intent', '') or ''),
                    question,
                    q_norm,
                    answer,
                    combined,
                    tok_ans,
                    tok_all,
                    None,
                ))

                # Q embedding (use normalized question; upstream may expand if needed)
                q_vec = self.get_embedding(q_norm or question)
                if q_vec:
                    q_rows.append((chunk_id_q, chunk_id, EMBEDDING_MODEL, EMBEDDING_DIMENSION, q_vec))

                # A embedding via chunking → per-chunk embeddings → mean
                a_chunks = chunk_answer_by_rule(answer)
                a_vecs = []
                for c in a_chunks:
                    v = self.get_embedding(c)
                    if v:
                        a_vecs.append(v)
                    time.sleep(RATE_LIMIT_DELAY)  # polite pacing within batch

                a_vec = avg_vectors(a_vecs) if a_vecs else None
                if a_vec:
                    a_rows.append((chunk_id, EMBEDDING_MODEL, EMBEDDING_DIMENSION, a_vec))

                ok += 1

                # Flush in batches
                if len(meta_rows) >= BATCH_SIZE:
                    self.insert_metadata_batch(meta_rows)
                    meta_rows = []
                if len(q_rows) >= BATCH_SIZE:
                    self.insert_q_batch(q_rows)
                    q_rows = []
                if len(a_rows) >= BATCH_SIZE:
                    self.insert_a_batch(a_rows)
                    a_rows = []

            except Exception as e:
                err += 1
                print(f"\n✗ Row {i} failed: {e}")

        # final flush
        if meta_rows:
            self.insert_metadata_batch(meta_rows)
        if q_rows:
            self.insert_q_batch(q_rows)
        if a_rows:
            self.insert_a_batch(a_rows)

        print(f"\n✅ Done. Success: {ok}, Errors: {err}, Total: {total}")

# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Embed interview Q/A with chunked answer embeddings (mean pooling)")
    parser.add_argument("--input", required=True, help="Path to CSV (must include 'question','answer' cols)")
    args = parser.parse_args()

    E = Embedder(args.input)
    E.connect_db()
    try:
        E.process()
    finally:
        E.close_db()

if __name__ == "__main__":
    main()

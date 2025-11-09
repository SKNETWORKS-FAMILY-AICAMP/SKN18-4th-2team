#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interview Q&A Embedding Script
Inserts data into separated meta_df, vec_q_index, and vec_a_index tables
"""

import os
import sys
import re
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import time
from typing import List, Dict, Tuple
import tiktoken

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072
BATCH_SIZE = 50  # Smaller batch for better control
RATE_LIMIT_DELAY = 0.2  # Delay between API calls

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "interview_db"),
    "user": os.getenv("DB_USER", "interview_user"),
    "password": os.getenv("DB_PASSWORD", "interview_pass")
}


class InterviewEmbedder:
    """Handles embedding generation and storage for interview data"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.conn = None
        self.cursor = None
        # text-embedding-3-large uses cl100k_base encoding
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to database: {DB_CONFIG['database']}")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            sys.exit(1)
    
    def close_db(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")
    
    def load_data(self) -> pd.DataFrame:
        """Load CSV data"""
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            print(f"✓ Loaded {len(df)} records from {self.csv_path}")
            
            # Ensure required columns exist
            required_cols = ['question', 'answer']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            return df
        except Exception as e:
            print(f"✗ Failed to load CSV: {e}")
            sys.exit(1)
    
    def normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, remove extra spaces, remove special chars"""
        if not isinstance(text, str):
            return ""
        # Lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters (keep Korean, English, numbers, basic punctuation)
        text = re.sub(r'[^\w\sㄱ-ㅎ가-힣.,!?]', '', text)
        return text.strip()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.encoding.encode(text))
        except:
            return 0
    
    def create_chunk_id(self, doc_id: int, suffix: str = "") -> str:
        """Create unique chunk_id"""
        if suffix:
            return f"DOC{doc_id:06d}_{suffix}"
        return f"DOC{doc_id:06d}"
    
    def create_content_combined(self, question: str, answer: str) -> str:
        """Create combined Q&A text"""
        return f"Q: {question}\nA: {answer}"
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"✗ Embedding generation failed: {e}")
            return None
    
    def insert_metadata_batch(self, batch_data: List[tuple]):
        """Insert batch of metadata records"""
        query = """
        INSERT INTO qa.meta_df (
            chunk_id, doc_id, occupation, gender, age_range, experience,
            answer_intent_category, answer_emotion_expression, answer_emotion_category,
            question_intent, question_text, question_text_norm, answer_text,
            content_combined, tokens_answer, tokens_combined, group_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (chunk_id) DO NOTHING
        """
        try:
            execute_batch(self.cursor, query, batch_data)
            self.conn.commit()
        except Exception as e:
            print(f"✗ Metadata batch insert failed: {e}")
            self.conn.rollback()
            raise
    
    def insert_q_embedding_batch(self, batch_data: List[tuple]):
        """Insert batch of Q-Index embeddings"""
        query = """
        INSERT INTO qa.vec_q_index (chunk_id_q, chunk_id, emb_model, emb_dim, embedding)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (chunk_id_q) DO UPDATE SET
            embedding = EXCLUDED.embedding,
            emb_model = EXCLUDED.emb_model,
            emb_dim = EXCLUDED.emb_dim
        """
        try:
            execute_batch(self.cursor, query, batch_data)
            self.conn.commit()
        except Exception as e:
            print(f"✗ Q-Index batch insert failed: {e}")
            self.conn.rollback()
            raise
    
    def insert_a_embedding_batch(self, batch_data: List[tuple]):
        """Insert batch of A-Index embeddings"""
        query = """
        INSERT INTO qa.vec_a_index (chunk_id, emb_model, emb_dim, embedding)
        VALUES (%s, %s, %s, %s)
        """
        try:
            execute_batch(self.cursor, query, batch_data)
            self.conn.commit()
        except Exception as e:
            print(f"✗ A-Index batch insert failed: {e}")
            self.conn.rollback()
            raise
    
    def check_existing_count(self) -> Dict[str, int]:
        """Check existing record counts"""
        counts = {}
        try:
            self.cursor.execute("SELECT COUNT(*) FROM qa.meta_df")
            counts['meta'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM qa.vec_q_index")
            counts['q_index'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM qa.vec_a_index")
            counts['a_index'] = self.cursor.fetchone()[0]
            
            return counts
        except Exception as e:
            print(f"⚠ Could not check existing counts: {e}")
            return {'meta': 0, 'q_index': 0, 'a_index': 0}
    
    def clear_all_data(self):
        """Clear all data from tables"""
        response = input("⚠ Clear ALL existing data? (yes/no): ")
        if response.lower() == 'yes':
            try:
                self.cursor.execute("TRUNCATE TABLE qa.vec_a_index CASCADE")
                self.cursor.execute("TRUNCATE TABLE qa.vec_q_index CASCADE")
                self.cursor.execute("TRUNCATE TABLE qa.meta_df CASCADE")
                self.conn.commit()
                print("✓ All data cleared")
            except Exception as e:
                print(f"✗ Failed to clear data: {e}")
                self.conn.rollback()
    
    def process_embeddings(self):
        """Main processing function"""
        # Load data
        df = self.load_data()
        
        # Check existing records
        existing = self.check_existing_count()
        if any(existing.values()):
            print(f"\n⚠ Existing records found:")
            print(f"   meta_df: {existing['meta']}")
            print(f"   vec_q_index: {existing['q_index']}")
            print(f"   vec_a_index: {existing['a_index']}")
            self.clear_all_data()
        
        # Prepare batches
        total_records = len(df)
        meta_batch = []
        q_batch = []
        a_batch = []
        
        success_count = 0
        error_count = 0
        
        print(f"\n🚀 Starting embedding generation for {total_records} records...")
        print(f"Model: {EMBEDDING_MODEL} (dimension: {EMBEDDING_DIMENSION})")
        print(f"Schema: qa (meta_df, vec_q_index, vec_a_index)\n")
        
        for idx, row in tqdm(df.iterrows(), total=total_records, desc="Processing"):
            try:
                # Generate IDs
                doc_id = int(row.get('sample_id', idx + 1)) if pd.notna(row.get('sample_id')) else idx + 1
                chunk_id = self.create_chunk_id(doc_id)
                chunk_id_q = self.create_chunk_id(doc_id, "Q")
                
                # Extract texts
                question_text = str(row['question'])
                answer_text = str(row['answer'])
                question_text_norm = self.normalize_text(question_text)
                content_combined = self.create_content_combined(question_text, answer_text)
                
                # Count tokens
                tokens_answer = self.count_tokens(answer_text)
                tokens_combined = self.count_tokens(content_combined)
                
                # Prepare metadata
                meta_record = (
                    chunk_id,
                    doc_id,
                    str(row.get('occupation', '')),
                    str(row.get('gender', '')),
                    str(row.get('ageRange', '')),
                    str(row.get('experience', '')),
                    str(row.get('answer-intent_category', '')),
                    str(row.get('answer-emotion_expression', '')),
                    str(row.get('answer-emotion_category', '')),
                    str(row.get('question_intent', '')),
                    question_text,
                    question_text_norm,
                    answer_text,
                    content_combined,
                    tokens_answer,
                    tokens_combined,
                    None  # group_id - can be populated later
                )
                meta_batch.append(meta_record)
                
                # Generate Q embedding
                q_embedding = self.get_embedding(question_text_norm or question_text)
                if q_embedding:
                    q_record = (
                        chunk_id_q,
                        chunk_id,
                        EMBEDDING_MODEL,
                        EMBEDDING_DIMENSION,
                        q_embedding
                    )
                    q_batch.append(q_record)
                
                # Generate A embedding
                a_embedding = self.get_embedding(answer_text)
                if a_embedding:
                    a_record = (
                        chunk_id,
                        EMBEDDING_MODEL,
                        EMBEDDING_DIMENSION,
                        a_embedding
                    )
                    a_batch.append(a_record)
                
                success_count += 1
                
                # Insert batches when size reached
                if len(meta_batch) >= BATCH_SIZE:
                    self.insert_metadata_batch(meta_batch)
                    self.insert_q_embedding_batch(q_batch)
                    self.insert_a_embedding_batch(a_batch)
                    meta_batch = []
                    q_batch = []
                    a_batch = []
                
                # Rate limiting
                time.sleep(RATE_LIMIT_DELAY)
                
            except Exception as e:
                print(f"\n✗ Error processing record {idx} (doc_id={doc_id}): {e}")
                error_count += 1
        
        # Insert remaining records
        if meta_batch:
            self.insert_metadata_batch(meta_batch)
            self.insert_q_embedding_batch(q_batch)
            self.insert_a_embedding_batch(a_batch)
        
        # Final stats
        final_counts = self.check_existing_count()
        
        print(f"\n✅ Embedding generation completed!")
        print(f"   Processed: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   Total: {total_records}")
        print(f"\n📊 Final database counts:")
        print(f"   meta_df: {final_counts['meta']}")
        print(f"   vec_q_index: {final_counts['q_index']}")
        print(f"   vec_a_index: {final_counts['a_index']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate embeddings for interview Q&A data")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    args = parser.parse_args()
    
    if not OPENAI_API_KEY:
        print("✗ OPENAI_API_KEY not found in .env file")
        sys.exit(1)
    
    embedder = InterviewEmbedder(args.input)
    
    try:
        embedder.connect_db()
        embedder.process_embeddings()
    except KeyboardInterrupt:
        print("\n⚠ Process interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        embedder.close_db()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vector Similarity Search for Interview Q&A Database
Supports Q-Index, A-Index, and Hybrid search
"""

import os
import sys
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "interview_db"),
    "user": os.getenv("DB_USER", "interview_user"),
    "password": os.getenv("DB_PASSWORD", "interview_pass")
}


class VectorSearch:
    """Vector similarity search for interview embeddings"""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.conn = None
        self.cursor = None
    
    def connect_db(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to database")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            sys.exit(1)
    
    def close_db(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query"""
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=query,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"✗ Failed to generate query embedding: {e}")
            return None
    
    def search_questions(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """
        Search Q-Index (question embeddings only)
        
        Args:
            query: Search query text
            top_k: Number of results
            filters: {'occupation': 'ARD', 'question_intent': 'behavioral_star'}
        """
        query_embedding = self.get_query_embedding(query)
        if query_embedding is None:
            return []
        
        # Call stored function
        sql = """
        SELECT * FROM qa.search_questions(
            %s::vector(3072),
            %s,
            %s,
            %s
        )
        """
        
        occupation = filters.get('occupation') if filters else None
        q_intent = filters.get('question_intent') if filters else None
        
        try:
            self.cursor.execute(sql, (query_embedding, top_k, occupation, q_intent))
            results = []
            
            for row in self.cursor.fetchall():
                results.append({
                    'chunk_id': row[0],
                    'doc_id': row[1],
                    'question_text': row[2],
                    'answer_text': row[3],
                    'similarity': float(row[4]),
                    'occupation': row[5],
                    'question_intent': row[6],
                    'answer_intent': row[7]
                })
            
            return results
            
        except Exception as e:
            print(f"✗ Q-Index search failed: {e}")
            return []
    
    def search_answers(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """
        Search A-Index (answer embeddings only)
        
        Args:
            query: Search query text
            top_k: Number of results
            filters: {'occupation': 'ARD', 'answer_intent': 'attitude'}
        """
        query_embedding = self.get_query_embedding(query)
        if query_embedding is None:
            return []
        
        # Call stored function
        sql = """
        SELECT * FROM qa.search_answers(
            %s::vector(3072),
            %s,
            %s,
            %s
        )
        """
        
        occupation = filters.get('occupation') if filters else None
        a_intent = filters.get('answer_intent') if filters else None
        
        try:
            self.cursor.execute(sql, (query_embedding, top_k, occupation, a_intent))
            results = []
            
            for row in self.cursor.fetchall():
                results.append({
                    'chunk_id': row[0],
                    'doc_id': row[1],
                    'question_text': row[2],
                    'answer_text': row[3],
                    'content_combined': row[4],
                    'similarity': float(row[5]),
                    'occupation': row[6],
                    'answer_intent': row[7]
                })
            
            return results
            
        except Exception as e:
            print(f"✗ A-Index search failed: {e}")
            return []
    
    def search_hybrid(self, query: str, top_k: int = 10, k_q: int = 3, filters: Dict = None) -> List[Dict]:
        """
        Hybrid search (combines A-Index and Q-Index results)
        
        Args:
            query: Search query text
            top_k: Total number of results
            k_q: Number of Q-Index results (rest from A-Index)
            filters: {'occupation': 'ARD'}
        """
        query_embedding = self.get_query_embedding(query)
        if query_embedding is None:
            return []
        
        # Call stored function
        sql = """
        SELECT * FROM qa.search_hybrid(
            %s::vector(3072),
            %s,
            %s,
            %s
        )
        """
        
        occupation = filters.get('occupation') if filters else None
        
        try:
            self.cursor.execute(sql, (query_embedding, top_k, k_q, occupation))
            results = []
            
            for row in self.cursor.fetchall():
                results.append({
                    'chunk_id': row[0],
                    'doc_id': row[1],
                    'question_text': row[2],
                    'answer_text': row[3],
                    'source_index': row[4],  # 'Q' or 'A'
                    'similarity': float(row[5]),
                    'occupation': row[6]
                })
            
            return results
            
        except Exception as e:
            print(f"✗ Hybrid search failed: {e}")
            return []
    
    def display_results(self, results: List[Dict], search_type: str = ""):
        """Display search results"""
        if not results:
            print("No results found.")
            return
        
        print(f"\n{'='*80}")
        print(f"Found {len(results)} results{f' ({search_type})' if search_type else ''}:")
        print(f"{'='*80}\n")
        
        for i, result in enumerate(results, 1):
            print(f"[Result {i}] Similarity: {result['similarity']:.4f}")
            print(f"Chunk ID: {result['chunk_id']} | Doc ID: {result['doc_id']}")
            
            if 'source_index' in result:
                print(f"Source: {result['source_index']}-Index")
            
            if 'occupation' in result:
                print(f"Occupation: {result['occupation']}")
            
            if 'question_intent' in result:
                print(f"Question Intent: {result['question_intent']}")
            
            if 'answer_intent' in result:
                print(f"Answer Intent: {result['answer_intent']}")
            
            print(f"\n질문: {result['question_text']}")
            
            answer_preview = result['answer_text'][:300]
            if len(result['answer_text']) > 300:
                answer_preview += "..."
            print(f"\n답변: {answer_preview}")
            print(f"\n{'-'*80}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Search for similar interview Q&A")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--mode", choices=['q', 'a', 'hybrid'], default='hybrid', 
                        help="Search mode: q (Q-Index), a (A-Index), hybrid (both)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--k-q", type=int, default=2, help="Q-Index results in hybrid mode (default: 2)")
    parser.add_argument("--occupation", help="Filter by occupation")
    parser.add_argument("--q-intent", help="Filter by question intent (Q-Index only)")
    parser.add_argument("--a-intent", help="Filter by answer intent (A-Index only)")
    args = parser.parse_args()
    
    if not OPENAI_API_KEY:
        print("✗ OPENAI_API_KEY not found in .env file")
        sys.exit(1)
    
    # Build filters
    filters = {}
    if args.occupation:
        filters['occupation'] = args.occupation
    if args.q_intent:
        filters['question_intent'] = args.q_intent
    if args.a_intent:
        filters['answer_intent'] = args.a_intent
    
    # Search
    searcher = VectorSearch()
    
    try:
        searcher.connect_db()
        print(f"\n🔍 Searching for: '{args.query}'")
        print(f"📋 Mode: {args.mode.upper()}-Index")
        if filters:
            print(f"🔎 Filters: {filters}")
        
        if args.mode == 'q':
            results = searcher.search_questions(args.query, top_k=args.top_k, filters=filters)
            search_type = "Q-Index"
        elif args.mode == 'a':
            results = searcher.search_answers(args.query, top_k=args.top_k, filters=filters)
            search_type = "A-Index"
        else:  # hybrid
            results = searcher.search_hybrid(args.query, top_k=args.top_k, k_q=args.k_q, filters=filters)
            search_type = "Hybrid"
        
        searcher.display_results(results, search_type)
        
    except KeyboardInterrupt:
        print("\n⚠ Search interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        searcher.close_db()


if __name__ == "__main__":
    main()

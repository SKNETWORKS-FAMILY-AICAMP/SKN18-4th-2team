"""
임베더 로딩 유틸
"""
# vectordb/embedder.py (코사인 최적화 버전)
import time
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class RAGEmbedder:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large-instruct"):
        self.model_name = model_name
        self._use_instruction_format = "e5" in model_name.lower()
        self.model = self._load_model()

    def _load_model(self):
        """
        SentenceTransformer 기반 임베딩 모델을 로드합니다.
        """
        print(f"임베딩 모델 로드 중: {self.model_name}")
        start_time = time.time()

        try:
            model = SentenceTransformer(self.model_name)

            print(f"모델 로드 완료. ({time.time() - start_time:.2f}초)")
            return model
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            raise

    def _format_passages(self, texts: List[str]) -> List[str]:
        if not self._use_instruction_format:
            return texts

        formatted = []
        for text in texts:
            cleaned = (text or "").strip()
            if cleaned.lower().startswith("passage:"):
                formatted.append(cleaned)
            else:
                formatted.append(f"passage: {cleaned}")
        return formatted

    def embed_texts(self, texts: List[str], batch_size: int = 64, normalize: bool = True) -> np.ndarray:
        """텍스트 목록을 배치 단위로 임베딩합니다."""
        if self.model is None:
            raise Exception("모델이 로드되지 않았습니다.")

        formatted_texts = self._format_passages(texts)
        print(f"{len(formatted_texts)}개 텍스트 임베딩 작업 (배치 크기: {batch_size}, 정규화: {normalize})...")
        start_time = time.time()

        embeddings = self.model.encode(
            formatted_texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
        )

        print(f"임베딩 완료. ({time.time() - start_time:.2f}초)")
        return embeddings

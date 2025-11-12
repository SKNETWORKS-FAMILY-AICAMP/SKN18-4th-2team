import os
from functools import lru_cache
from typing import Tuple, Any

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI


@lru_cache(maxsize=1) # 함수 결과를 메모리에 저장해 두는 파이썬 표준 라이브러리
def _load_embeddings():
    backend = os.getenv("EMBEDDING_BACKEND")
    model_name = os.getenv("LOCAL_EMBEDDING_MODEL")

    if backend == "openai":
        embeddings_model = OpenAIEmbeddings(model=model_name)

    elif backend == "huggingface":
        normalize = os.getenv("LOCAL_EMBEDDING_NORMALIZE", "false").lower() == "true"
        embeddings_model = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": normalize},
        )

    dim_env = os.getenv("LOCAL_EMBEDDING_DIM")
    if dim_env:
        dimension = int(dim_env)
    else:
        dimension = len(embeddings_model.embed_query("dimension probe"))
    return embeddings_model, dimension


def get_embedding_model():
    """Return the cached embedding model instance."""
    return _load_embeddings()[0]


def get_embedding_dim() -> int:
    """Return the embedding dimension for the current model."""
    return _load_embeddings()[1]

@lru_cache(maxsize=2)
def load_openai_model(*, params_key: Tuple[Tuple[str, Any], ...]) -> ChatOpenAI:
    """답변생성 혹은 평가 모델을 로드하는 함수"""
    params = dict(params_key)
    return ChatOpenAI(**params)

@lru_cache(maxsize=1) 
def load_ollama_model() -> ChatOllama:
    """채Ollama LLM을 초기화"""
    model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    temperature = float(os.getenv("CLASSIFY_TEMPERATURE", "0.2"))
    return ChatOllama(model=model, temperature=temperature)

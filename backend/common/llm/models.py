from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .utils import set_openapi


def set_embedding_model(model_name: str = "text-embedding-3-large") -> OpenAIEmbeddings:
    """Instantiate the embedding model used for vector operations."""
    return OpenAIEmbeddings(
        model=model_name,
        openai_api_key=set_openapi(),
    )


def set_classify_model(model_name: str = "gpt-4o-mini") -> ChatOpenAI:
    """Return the classifier model for routing questions."""
    return ChatOpenAI(
        model=model_name,
        openai_api_key=set_openapi(),
        temperature=0,
    )


def set_llm_model(model_name: str = "gpt-5-nano") -> ChatOpenAI:
    """Return the main chat model for answer generation."""
    return ChatOpenAI(
        model=model_name,
        openai_api_key=set_openapi(),
        reasoning_effort="high",
    )


def set_score_model(model_name: str = "gpt-5-nano") -> ChatOpenAI:
    """Return the model used to score document relevance."""
    return ChatOpenAI(
        model=model_name,
        openai_api_key=set_openapi(),
        frequency_penalty=0,
    )

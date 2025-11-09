import os
from functools import lru_cache


@lru_cache(maxsize=1)
def set_openapi() -> str:

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
    return api_key

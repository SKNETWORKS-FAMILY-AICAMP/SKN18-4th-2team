from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str, model="text-embedding-3-large"):
    if not text or not text.strip():
        return []
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding

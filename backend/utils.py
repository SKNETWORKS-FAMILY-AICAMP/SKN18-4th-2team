import os


def make_conn_str() -> str:
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    user = os.getenv("POSTGRES_USER")
    pwd = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"


import os
from typing import Any, Dict
from urllib.parse import urlparse

from .Singleton import SingletonDatabase


def _pool_limits() -> Dict[str, int]:
    return {
        "minconn": 1,
        "maxconn": 5,
    }


def _config_from_url(conn_url: str) -> Dict[str, Any]:
    url = urlparse(conn_url)
    path = url.path.lstrip("/")
    return {
        "dsn": conn_url,
        "dbname": path,
        **_pool_limits(),
    }


def _config_from_env() -> Dict[str, Any]:
    required = ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"환경 변수 {', '.join(missing)} 가 설정되어 있지 않습니다.")

    return {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        **_pool_limits(),
    }


def connect_DB(connect_str: str = "CONNECTION_STRING") -> SingletonDatabase:
    """Return a singleton database pool using either a DSN or discrete env vars."""
    conn_url = os.getenv(connect_str)
    if conn_url:
        if isinstance(conn_url, bytes):
            conn_url = conn_url.decode()
        config = _config_from_url(conn_url)
    else:
        config = _config_from_env()

    return SingletonDatabase(config)

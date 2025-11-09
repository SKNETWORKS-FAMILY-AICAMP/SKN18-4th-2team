import threading
from typing import Any, Dict, Optional

from pgvector.psycopg2 import register_vector
from psycopg2.pool import SimpleConnectionPool


class SingletonDatabase:
    """Very small thread-safe connection pool for pgvector operations."""

    _instance: Optional["SingletonDatabase"] = None
    _lock = threading.Lock()

    def __new__(cls, config: Dict[str, Any]):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_pool(config)
        return cls._instance

    def _init_pool(self, config: Dict[str, Any]) -> None:
        pool_config = config.copy()
        minconn = pool_config.pop("minconn", 1)
        maxconn = pool_config.pop("maxconn", 5)
        dsn = pool_config.pop("dsn", None)

        if dsn:
            self._pool = SimpleConnectionPool(minconn, maxconn, dsn)  # type: ignore[arg-type]
        else:
            self._pool = SimpleConnectionPool(minconn, maxconn, **pool_config)

    def get_connection(self):
        conn = self._pool.getconn()
        register_vector(conn)
        return conn

    def put_connection(self, conn) -> None:
        if conn is not None:
            self._pool.putconn(conn)

    def close_all(self) -> None:
        self._pool.closeall()

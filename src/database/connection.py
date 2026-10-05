import os
import threading
from typing import Optional
from unittest.mock import Mock

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection
from dotenv import load_dotenv


load_dotenv()

_POOL: Optional[MySQLConnectionPool] = None
_POOL_LOCK = threading.Lock()


def _get_db_param(key: str, default: str = "") -> str:
    """Helper to retrieve configuration from environment or Streamlit secrets."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


def get_connection_pool(pool_name: str = "quantdb_pool", pool_size: int = 5) -> Optional[MySQLConnectionPool]:
    """
    Initializes or returns the singleton thread-safe MySQL connection pool.
    Pool size is configurable via DB_POOL_SIZE environment variable.
    """
    global _POOL
    if _POOL is not None:
        return _POOL

    with _POOL_LOCK:
        if _POOL is not None:
            return _POOL

        host = _get_db_param("DB_HOST", "localhost")
        port = int(_get_db_param("DB_PORT", "3306"))
        database = _get_db_param("DB_NAME", "QuantDB")
        user = _get_db_param("DB_USER", "root")
        password = _get_db_param("DB_PASSWORD", "")
        custom_size_str = _get_db_param("DB_POOL_SIZE", str(pool_size))
        try:
            pool_size_val = int(custom_size_str)
        except ValueError:
            pool_size_val = pool_size

        try:
            _POOL = MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size_val,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                pool_reset_session=True,
            )
            return _POOL
        except Error as error:
            # Mask credentials from error message
            safe_msg = str(error).replace(password, "******") if password else str(error)
            print(f"Database connection pool initialization error: {safe_msg}")
            return None


def reset_connection_pool() -> None:
    """Resets the singleton connection pool instance."""
    global _POOL
    with _POOL_LOCK:
        _POOL = None


def get_connection(use_pool: bool = True):
    """
    Create or retrieve a connection to the QuantDB MySQL database.
    Uses MySQLConnectionPool for REAL mode efficiency and connection reuse.
    Gracefully falls back to direct connection if pool is exhausted or unavailable.
    Preserves direct connection for test mocks and explicit requests.
    """
    # If connect is patched with a mock (e.g., in unit tests) or pooling explicitly disabled
    is_mocked = isinstance(mysql.connector.connect, Mock)
    use_pool_env = _get_db_param("DB_USE_POOL", "true").lower() in ("true", "1", "yes")

    if not is_mocked and use_pool and use_pool_env:
        pool = get_connection_pool()
        if pool is not None:
            try:
                pooled_conn = pool.get_connection()
                # Test connection vitality and auto-reconnect if dropped
                try:
                    if hasattr(pooled_conn, "ping"):
                        pooled_conn.ping(reconnect=True, attempts=3, delay=1)
                except Exception:
                    pass

                if pooled_conn.is_connected():
                    return pooled_conn
            except Error as pool_err:
                print(f"Connection pool exhausted or error ({pool_err}); falling back to direct connection.")

    # Direct connection fallback / test mock path
    host = _get_db_param("DB_HOST", "localhost")
    port = int(_get_db_param("DB_PORT", "3306"))
    database = _get_db_param("DB_NAME", "QuantDB")
    user = _get_db_param("DB_USER", "root")
    password = _get_db_param("DB_PASSWORD", "")

    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )

        if connection.is_connected():
            return connection

        return None

    except Error as error:
        safe_msg = str(error).replace(password, "******") if password else str(error)
        print(f"Database direct connection error: {safe_msg}")
        return None


if __name__ == "__main__":
    connection = get_connection()

    if connection:
        print("QuantDB database connection successful!")
        connection.close()
    else:
        print("QuantDB database connection failed.")
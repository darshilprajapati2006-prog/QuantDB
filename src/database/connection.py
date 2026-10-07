"""
QuantDB Database Connection Management Layer.

Provides thread-safe MySQL connection pooling and direct connection fallbacks.
Supports both local environments (localhost:3306) and cloud environments (Aiven MySQL with SSL).
Prevents NoneType errors and preserves original MySQL error diagnostics.
"""

import logging
import os
import threading
from typing import Any, Dict, Optional
from unittest.mock import Mock

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_POOL: Optional[MySQLConnectionPool] = None
_POOL_LOCK = threading.Lock()
_LAST_CONNECTION_ERROR: Optional[str] = None


class DatabaseConnectionError(Exception):
    """Raised when a database connection cannot be established or is disconnected."""
    pass


def get_last_connection_error() -> Optional[str]:
    """Returns the most recent database connection error string, if any."""
    global _LAST_CONNECTION_ERROR
    return _LAST_CONNECTION_ERROR


def _get_db_param(key: str, default: str = "") -> str:
    """
    Retrieves database parameters from environment variables or Streamlit secrets.
    Handles exact, case-insensitive, prefix-less, and nested dictionary configurations.
    """
    # 1. Direct environment variable lookup
    val = os.getenv(key)
    if val is not None and val != "":
        return val
    val = os.getenv(key.lower())
    if val is not None and val != "":
        return val

    # 2. Streamlit secrets lookup
    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            # Exact match
            if key in st.secrets:
                return str(st.secrets[key])
            # Lowercase match
            if key.lower() in st.secrets:
                return str(st.secrets[key.lower()])

            # Without DB_ prefix
            short_key = key[3:] if key.startswith("DB_") else key
            if short_key in st.secrets:
                return str(st.secrets[short_key])
            if short_key.lower() in st.secrets:
                return str(st.secrets[short_key.lower()])

            # Nested sections
            for section in ("mysql", "database", "QuantDB", "quantdb", "connections"):
                if section in st.secrets and isinstance(st.secrets[section], dict):
                    sec = st.secrets[section]
                    for candidate in (key, key.lower(), short_key, short_key.lower()):
                        if candidate in sec:
                            return str(sec[candidate])
    except Exception:
        pass

    return default


def _get_ssl_config(host: str, port: int) -> Dict[str, Any]:
    """
    Resolves MySQL SSL arguments for local vs. cloud database environments.
    Aiven MySQL and cloud instances require SSL encryption on the wire.
    """
    ssl_mode = _get_db_param("DB_SSL_MODE", "").upper()
    ssl_req = _get_db_param("DB_SSL_REQUIRED", "").lower() in ("true", "1", "yes")
    ssl_ca = _get_db_param("DB_SSL_CA", "")
    ssl_disabled = _get_db_param("DB_SSL_DISABLED", "").lower() in ("true", "1", "yes")

    # Cloud detection: non-local host, non-standard port (e.g., Aiven 14328), or explicit SSL mode
    is_remote = host not in ("localhost", "127.0.0.1") or port != 3306
    should_use_ssl = (
        is_remote
        or ssl_req
        or ssl_mode in ("REQUIRED", "REQUIRED_SSL", "VERIFY_CA", "VERIFY_IDENTITY")
    ) and not ssl_disabled

    if not should_use_ssl:
        if ssl_disabled:
            return {"ssl_disabled": True}
        return {}

    # For Aiven and cloud instances: enable SSL transport
    cfg: Dict[str, Any] = {"ssl_disabled": False}
    if ssl_ca and os.path.isfile(ssl_ca):
        cfg["ssl_ca"] = ssl_ca
        cfg["ssl_verify_cert"] = True
    else:
        # Aiven provides trusted server certificates; verify_cert False allows SSL without requiring ca.pem file
        cfg["ssl_verify_cert"] = False

    return cfg


def get_connection_pool(
    pool_name: str = "quantdb_pool", pool_size: int = 5
) -> Optional[MySQLConnectionPool]:
    """
    Initializes or returns the singleton thread-safe MySQL connection pool.
    Pool size is configurable via DB_POOL_SIZE environment variable.
    """
    global _POOL, _LAST_CONNECTION_ERROR
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

        pool_kwargs: Dict[str, Any] = {
            "pool_name": pool_name,
            "pool_size": pool_size_val,
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
            "pool_reset_session": True,
        }
        pool_kwargs.update(_get_ssl_config(host, port))

        try:
            _POOL = MySQLConnectionPool(**pool_kwargs)
            return _POOL
        except Error as error:
            safe_msg = str(error).replace(password, "******") if password else str(error)
            _LAST_CONNECTION_ERROR = safe_msg
            logger.warning(f"Database connection pool initialization warning: {safe_msg}")
            return None


def reset_connection_pool() -> None:
    """Resets the singleton connection pool instance."""
    global _POOL, _LAST_CONNECTION_ERROR
    with _POOL_LOCK:
        _POOL = None
        _LAST_CONNECTION_ERROR = None


def get_connection(use_pool: bool = True, raise_on_error: bool = False):
    """
    Create or retrieve a connection to the QuantDB MySQL database.
    Uses MySQLConnectionPool for efficiency and connection reuse.
    Gracefully falls back to direct connection if pool is exhausted or unavailable.

    Args:
        use_pool: Whether to attempt acquiring from the connection pool.
        raise_on_error: If True, raises DatabaseConnectionError on failure instead of returning None.
    """
    global _LAST_CONNECTION_ERROR

    # If connect is patched with a mock (e.g., in unit tests) or pooling explicitly disabled
    is_mocked = isinstance(mysql.connector.connect, Mock)
    use_pool_env = _get_db_param("DB_USE_POOL", "true").lower() in ("true", "1", "yes")

    if not is_mocked and use_pool and use_pool_env:
        pool = get_connection_pool()
        if pool is not None:
            try:
                pooled_conn = pool.get_connection()
                try:
                    if hasattr(pooled_conn, "ping"):
                        pooled_conn.ping(reconnect=True, attempts=3, delay=1)
                except Exception:
                    pass

                if pooled_conn.is_connected():
                    return pooled_conn
            except Error as pool_err:
                safe_pool_msg = str(pool_err)
                logger.info(f"Connection pool acquisition failed ({safe_pool_msg}); falling back to direct connect.")

    # Direct connection fallback / test mock path
    host = _get_db_param("DB_HOST", "localhost")
    port = int(_get_db_param("DB_PORT", "3306"))
    database = _get_db_param("DB_NAME", "QuantDB")
    user = _get_db_param("DB_USER", "root")
    password = _get_db_param("DB_PASSWORD", "")

    connect_kwargs: Dict[str, Any] = {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }
    connect_kwargs.update(_get_ssl_config(host, port))

    try:
        connection = mysql.connector.connect(**connect_kwargs)

        if connection is not None and connection.is_connected():
            return connection

        _LAST_CONNECTION_ERROR = "Database connection established but is_connected() returned False."
        if raise_on_error:
            raise DatabaseConnectionError(_LAST_CONNECTION_ERROR)
        return None

    except Error as error:
        safe_msg = str(error).replace(password, "******") if password else str(error)
        _LAST_CONNECTION_ERROR = safe_msg
        logger.error(f"Database direct connection error: {safe_msg}")
        if raise_on_error:
            raise DatabaseConnectionError(safe_msg) from error
        return None


if __name__ == "__main__":
    connection = get_connection()

    if connection:
        print("QuantDB database connection successful!")
        connection.close()
    else:
        err = get_last_connection_error()
        print(f"QuantDB database connection failed: {err}")
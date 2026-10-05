import os
from unittest.mock import patch, MagicMock
import pytest
from mysql.connector import Error
from mysql.connector.errors import PoolError

from src.database.connection import (
    get_connection,
    get_connection_pool,
    reset_connection_pool,
)


class TestConnectionPooling:
    """Tests for MySQL connection pooling functionality in QuantDB."""

    def setup_method(self):
        reset_connection_pool()

    def teardown_method(self):
        reset_connection_pool()

    @patch("src.database.connection.MySQLConnectionPool")
    def test_pool_singleton(self, mock_pool_cls):
        """Test that get_connection_pool returns the same pool instance on repeated calls."""
        mock_instance = MagicMock()
        mock_pool_cls.return_value = mock_instance

        pool1 = get_connection_pool(pool_name="test_pool", pool_size=5)
        pool2 = get_connection_pool(pool_name="test_pool", pool_size=5)

        assert pool1 is mock_instance
        assert pool2 is mock_instance
        mock_pool_cls.assert_called_once()

    @patch("src.database.connection.get_connection_pool")
    def test_get_connection_uses_pool(self, mock_get_pool):
        """Test that get_connection acquires a connection from the pool."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_pool.get_connection.return_value = mock_conn
        mock_get_pool.return_value = mock_pool

        conn = get_connection(use_pool=True)

        assert conn is mock_conn
        mock_pool.get_connection.assert_called_once()
        mock_conn.ping.assert_called_once()

    @patch("src.database.connection.mysql.connector.connect")
    @patch("src.database.connection.get_connection_pool")
    def test_pool_fallback_on_error(self, mock_get_pool, mock_connect):
        """Test that pool failure falls back to direct connect gracefully."""
        mock_pool = MagicMock()
        mock_pool.get_connection.side_effect = PoolError("Failed getting connection; pool exhausted")
        mock_get_pool.return_value = mock_pool

        direct_conn = MagicMock()
        direct_conn.is_connected.return_value = True
        mock_connect.return_value = direct_conn

        conn = get_connection(use_pool=True)

        assert conn is direct_conn
        mock_connect.assert_called_once()

    @patch("src.database.connection.MySQLConnectionPool")
    def test_credentials_not_exposed_on_pool_error(self, mock_pool_cls, capsys):
        """Test that credentials are not leaked to stderr/stdout on pool initialization error."""
        secret_pass = "super_secret_db_pass_12345"
        mock_pool_cls.side_effect = Error(f"Access denied for user 'root' with password '{secret_pass}'")

        with patch.dict(os.environ, {"DB_PASSWORD": secret_pass}):
            pool = get_connection_pool()

        captured = capsys.readouterr()
        assert pool is None
        assert secret_pass not in captured.out
        assert secret_pass not in captured.err

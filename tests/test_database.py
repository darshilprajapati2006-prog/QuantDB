import os
from unittest.mock import patch, MagicMock

import pytest
from mysql.connector import Error

from src.database.connection import get_connection


class TestDatabaseConnection:
    """Tests for QuantDB database connection."""

    @patch("src.database.connection.mysql.connector.connect")
    def test_successful_connection(self, mock_connect):
        """Test that a successful MySQL connection is returned."""

        mock_connection = MagicMock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        connection = get_connection()

        assert connection is mock_connection
        mock_connect.assert_called_once()

    @patch("src.database.connection.mysql.connector.connect")
    def test_connection_failure(self, mock_connect):
        """Test that connection failure returns None."""

        mock_connect.side_effect = Error("Unable to connect to database")

        connection = get_connection()

        assert connection is None

    @patch("src.database.connection.mysql.connector.connect")
    def test_connection_parameters(self, mock_connect):
        """Test that correct environment variables are passed to MySQL."""

        mock_connection = MagicMock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        with patch.dict(
            os.environ,
            {
                "DB_HOST": "localhost",
                "DB_PORT": "3306",
                "DB_NAME": "quantdb",
                "DB_USER": "root",
                "DB_PASSWORD": "test_password",
            },
        ):
            connection = get_connection()

        assert connection is mock_connection

        mock_connect.assert_called_once_with(
            host="localhost",
            port=3306,
            database="quantdb",
            user="root",
            password="test_password",
        )

    @patch("src.database.connection.mysql.connector.connect")
    def test_disconnected_connection_returns_none(self, mock_connect):
        """Test that a connection object that is not connected returns None."""

        mock_connection = MagicMock()
        mock_connection.is_connected.return_value = False
        mock_connect.return_value = mock_connection

        connection = get_connection()

        assert connection is None

    @patch("src.database.connection.mysql.connector.connect")
    def test_connection_uses_default_port(self, mock_connect):
        """Test that MySQL port defaults to 3306."""

        mock_connection = MagicMock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        with patch.dict(
            os.environ,
            {
                "DB_HOST": "localhost",
                "DB_NAME": "quantdb",
                "DB_USER": "root",
                "DB_PASSWORD": "test_password",
            },
            clear=True,
        ):
            connection = get_connection()

        assert connection is mock_connection

        mock_connect.assert_called_once_with(
            host="localhost",
            port=3306,
            database="quantdb",
            user="root",
            password="test_password",
        )

    @patch("src.database.connection.mysql.connector.connect")
    def test_aiven_cloud_ssl_parameters_passed(self, mock_connect):
        """Test that Aiven remote host with port 14328 passes SSL parameters."""
        mock_connection = MagicMock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        with patch.dict(
            os.environ,
            {
                "DB_HOST": "quantdb-mysql-darshilprajapati2006-a582.d.aivencloud.com",
                "DB_PORT": "14328",
                "DB_NAME": "QuantDB",
                "DB_USER": "avnadmin",
                "DB_PASSWORD": "secret_password",
            },
            clear=True,
        ):
            connection = get_connection()

        assert connection is mock_connection
        mock_connect.assert_called_once_with(
            host="quantdb-mysql-darshilprajapati2006-a582.d.aivencloud.com",
            port=14328,
            database="QuantDB",
            user="avnadmin",
            password="secret_password",
            ssl_disabled=False,
            ssl_verify_cert=False,
        )

    def test_repository_safe_close_on_none(self):
        """Test that Repository._close_conn handles None and objects without close() without raising AttributeError."""
        from src.database.repository import Repository
        repo = Repository()

        # None should be safely ignored
        repo._close_conn(None)

        # Object without close should be safely ignored
        repo._close_conn("not_a_connection")

        # Object with close should have close called
        mock_conn = MagicMock()
        repo._close_conn(mock_conn)
        mock_conn.close.assert_called_once()

    @patch("src.database.repository.get_connection")
    def test_repository_failed_connection_raises_database_connection_error(self, mock_get_conn):
        """Test that Repository raises DatabaseConnectionError when connection fails instead of NoneType.close()."""
        from src.database.repository import Repository
        from src.database.connection import DatabaseConnectionError

        mock_get_conn.side_effect = DatabaseConnectionError("Failed to connect to MySQL")
        repo = Repository()

        with pytest.raises(DatabaseConnectionError):
            repo.get_user_by_identifier("test_user")

    @patch("src.database.repository.get_connection")
    def test_authentication_db_failure_handles_cleanly(self, mock_get_conn):
        """Test that authentication failure due to database connection error does not crash with AttributeError."""
        from src.auth.service import authenticate_user, AuthenticationError
        from src.database.connection import DatabaseConnectionError

        mock_get_conn.side_effect = DatabaseConnectionError("Can't connect to MySQL server")

        with pytest.raises(AuthenticationError) as exc_info:
            authenticate_user("test_user", "password123")

        assert "Authentication service currently unavailable" in str(exc_info.value)
        assert "NoneType" not in str(exc_info.value)

    @patch("src.database.repository.get_connection")
    def test_registration_db_failure_handles_cleanly(self, mock_get_conn):
        """Test that registration failure due to database connection error does not crash with AttributeError."""
        from src.auth.service import register_user, RegistrationError
        from src.database.connection import DatabaseConnectionError

        mock_get_conn.side_effect = DatabaseConnectionError("Can't connect to MySQL server")

        with pytest.raises(RegistrationError) as exc_info:
            register_user(
                name="Test User",
                username="testuser123",
                email="testuser123@example.com",
                password="Password123!",
                confirm_password="Password123!",
            )

        assert "Registration database error" in str(exc_info.value)
        assert "NoneType" not in str(exc_info.value)
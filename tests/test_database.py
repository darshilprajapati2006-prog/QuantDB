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

    def test_schema_contract_queries_have_no_username_column(self):
        """Verifies that none of the user SQL queries reference a physical 'username' column."""
        from src.database import queries

        assert "username" not in queries.GET_USER_BY_ID.lower()
        assert "username" not in queries.GET_USER_BY_EMAIL.lower()
        assert "username" not in queries.GET_USER_BY_IDENTIFIER.lower()
        assert "username" not in queries.GET_ALL_USERS.lower()
        assert "username" not in queries.CREATE_USER.lower()
        assert "username" not in queries.UPDATE_UNVERIFIED_USER.lower()

    def test_create_user_inserts_actual_schema_columns(self):
        """Verifies that create_user only passes actual schema columns to SQL."""
        from src.database import queries
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_conn.cursor.return_value = mock_cursor

        user_id = queries.create_user(
            mock_conn,
            name="Alice Trader",
            email="alice@quantdb.local",
            password_hash="pbkdf2_hash_value",
            role="QUANT_TRADER",
            status="ACTIVE",
        )

        assert user_id == 42
        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]
        # SQL must insert into (name, email, password_hash, role, status, created_at)
        assert "username" not in sql.lower()
        assert len(params) == 6
        assert params[0] == "Alice Trader"
        assert params[1] == "alice@quantdb.local"
        assert params[2] == "pbkdf2_hash_value"
        assert params[3] == "QUANT_TRADER"
        assert params[4] == "ACTIVE"

    def test_normalize_user_dict_injects_fallback_username_and_verified(self):
        """Verifies that user dict from actual schema row is normalized with synthetic username and is_verified."""
        from src.database.queries import _normalize_user_dict

        # Actual Aiven schema row without username or is_verified
        raw_row = {
            "user_id": 10,
            "name": "Bob Smith",
            "email": "bob.smith@quantdb.local",
            "password_hash": "hash_xyz",
            "role": "USER",
            "status": "ACTIVE",
            "created_at": "2026-03-01 10:00:00",
        }

        normalized = _normalize_user_dict(raw_row)
        assert normalized["username"] == "bob.smith"
        assert normalized["is_verified"] is True
        assert normalized["name"] == "Bob Smith"

    @patch("src.database.repository.Repository._get_connection")
    def test_auth_login_with_actual_schema_row(self, mock_get_conn):
        """Verifies authentication succeeds when database returns actual schema without username column."""
        from src.auth.service import authenticate_user
        from src.auth.password import hash_password

        pwd_hash = hash_password("ValidPassword123!")
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Row as returned by Aiven MySQL (no username, no is_verified)
        mock_cursor.fetchone.return_value = {
            "user_id": 5,
            "name": "Aarav Sharma",
            "email": "aarav@quantdb.com",
            "password_hash": pwd_hash,
            "role": "ADMIN",
            "status": "ACTIVE",
            "created_at": "2026-01-05 10:00:00",
        }
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        profile = authenticate_user("aarav@quantdb.com", "ValidPassword123!")
        assert profile["user_id"] == 5
        assert profile["email"] == "aarav@quantdb.com"
        assert profile["role"] == "ADMIN"
        assert profile["username"] == "aarav"
        assert profile["is_verified"] is True
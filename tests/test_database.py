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
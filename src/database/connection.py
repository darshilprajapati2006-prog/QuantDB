import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


load_dotenv()


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


def get_connection():
    """
    Create and return a connection to the QuantDB MySQL database.
    Supports environment variables (.env) and Streamlit Cloud secrets securely.
    """

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
        print(f"Database connection error: {error}")
        return None


if __name__ == "__main__":
    connection = get_connection()

    if connection:
        print("QuantDB database connection successful!")
        connection.close()
    else:
        print("QuantDB database connection failed.")
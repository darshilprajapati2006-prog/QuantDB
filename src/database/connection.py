import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    """
    Create and return a connection to the QuantDB MySQL database.
    """

    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
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
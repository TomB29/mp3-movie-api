import sqlite3
from pathlib import Path


def get_connection(db_path):
    """Return a fresh connection with rows accessible by column name."""
    # TODO: create the parent directory, connect, and set sqlite3.Row.
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path):
    """Create the movie table if it does not exist."""
    # TODO: create the movie table if needed, commit, and close the connection.
    statement = """
    CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY,
    title VARCHAR(50), 
    release_year CHAR(4), 
    rating DECIMAL(2,1),
    genre VARCHAR(16)
    )"""
    connection = get_connection(db_path)
    try:
        connection.execute(statement)
        connection.commit()
    finally:
        connection.close()
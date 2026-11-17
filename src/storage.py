import logging
import sqlite3

import pandas as pd

from .database import get_connection, initialize_database

logger = logging.getLogger(__name__)
MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]


class MovieStorage:
    def __init__(self, db_path="data/movies.db"):
        self.db_path = db_path
        initialize_database(self.db_path)

    def save(self, df):
        """Replace all movie rows in one transaction."""
        # TODO: Convert missing values to Python None for SQL NULL.
        # DELETE the old rows, then INSERT all rows from df.
        # Commit only after all inserts succeed; roll back on SQLite errors.
        # Close the connection in finally. Log the saved row count at DEBUG.
        connection = get_connection(self.db_path)
        scrubbed = df.astype(object).where(df.notna(), None)
        new_rows = scrubbed.values.tolist()
        movie_columns_insert = ", ".join(MOVIE_COLUMNS)

        try:
            connection.execute("DELETE FROM movies")
            insert_frame = f"""INSERT INTO movies 
            ({movie_columns_insert})
            VALUES (?, ?, ?, ?)"""
            connection.executemany(insert_frame, new_rows)
            connection.commit()
            logger.debug(f"{len(new_rows)} rows saved")
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close()


    def get(self):
        """Return the four movie columns as a DataFrame, ordered by id."""

        connection = get_connection(self.db_path)
        movie_columns_insert = ", ".join(MOVIE_COLUMNS)

        get_insert = f"""SELECT {movie_columns_insert}
        FROM movies
        ORDER BY id ASC"""

        try:
            command_execution = connection.execute(get_insert)
            collection = command_execution.fetchall()
            logger.info(f"Retrieved movies tables from database")
        finally:
            connection.close()

        return pd.DataFrame(collection, columns=MOVIE_COLUMNS)




    def select_columns(self, columns, limit=5):
        """Return id plus the requested movie columns, ordered by id."""
        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")

        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")

        selected_columns = ", ".join(["id"] + columns)
        connection = get_connection(self.db_path)
        cursor = connection.cursor()

        try:
            # TODO: SELECT selected_columns from movies, ordered by id.
            # Use a placeholder for limit; fetch the rows.
            # Return a list of dictionaries and log at DEBUG.



            selected_columns_frame = f"""
            SELECT {selected_columns} FROM MOVIES
            ORDER BY id
            LIMIT ?"""

            cursor.execute(selected_columns_frame, (limit,))
            rows = cursor.fetchall()
            rows_dict = [dict(row) for row in rows]


        finally:
            connection.close()
        logger.debug(f"returned list of dictionaries; contains {len(rows_dict)} list elements")
        return rows_dict

    def count_movies(self):
        """Return the number of stored movies using SQL COUNT(*)."""
        try:
            connection = get_connection(self.db_path)
            query = """SELECT COUNT(*) AS total FROM movies"""
            count = connection.execute(query).fetchone()
        finally:
            connection.close()
        logger.debug(f"returned count of movies -- table contains {count['total']} elements")
        return count['total']
            

    def query_movies(self, columns, min_rating, limit):
        """Return selected fields from matching movies using SQL."""
        # TODO: validate columns as in select_columns().
        # SELECT id plus those columns and filter by minimum rating.
        # Sort by rating DESC then id ASC, and apply limit.
        # Return dictionaries and log the selected columns and row count at DEBUG.
        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")

        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")
        
        connection = get_connection(self.db_path)
        cursor = connection.cursor()

        placeholder_dict = {'m_r': min_rating, 'l': limit}
        selected_columns = ", ".join(["id"] + columns)

        try:
            query_frame = f"""SELECT {selected_columns} FROM movies
            WHERE rating >= :m_r
            ORDER BY rating DESC, id ASC
            LIMIT :l"""

            cursor.execute(query_frame, placeholder_dict)
            rows = cursor.fetchall()
            rows_dict = [dict(row) for row in rows]

        finally:
            connection.close()
        logger.debug(f"list of dictionaries returned -- {len(rows_dict)} rows")
        return rows_dict

    



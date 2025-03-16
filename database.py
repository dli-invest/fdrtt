import psycopg2
from psycopg2 import pool
import os
import pandas as pd

class DB_MANAGER:
    def __init__(self, pool_size=5):
        self.connection_pool = self.create_connection_pool(pool_size)

    def create_connection_pool(self, pool_size: int = 5):
        try:
            connection_string = os.environ.get("CONNECTION_STRING")
            if not connection_string:
                raise ValueError("CONNECTION_STRING environment variable not set.")
            return pool.ThreadedConnectionPool(1, pool_size, connection_string)
        except psycopg2.Error as e:
            print(f"Error creating connection pool: {e}")
            return None

    def get_connection_pool(self):
        return self.connection_pool

    def get_connection(self):
        try:
            return self.connection_pool.getconn()
        except psycopg2.Error as e:
            print(f"Error getting connection: {e}")
            return None

    def put_connection(self, conn):
        if conn:
            self.connection_pool.putconn(conn)

    def create_tables(self, video_id: str):
        conn = self.get_connection()
        if conn:
            try:
                fixed_id = video_id.replace("-", "_")
                cursor = conn.cursor()
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {fixed_id} (id SERIAL PRIMARY KEY, text TEXT, video_url VARCHAR(255), iteration INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
                )
                conn.commit()
            except psycopg2.Error as e:
                print(f"Error creating table: {e}")
            finally:
                if cursor:
                    cursor.close()
                self.put_connection(conn)

    def clear_table(self, video_id: str):
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {video_id}")
                conn.commit()
            except psycopg2.Error as e:
                print(f"Error clearing table: {e}")
            finally:
                if cursor:
                    cursor.close()
                self.put_connection(conn)

    def insert_into_db(self, video_id: str, text: str, video_url: str, iteration: int = 0):
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    f"INSERT INTO {video_id} (text, video_url, iteration) VALUES (%s, %s, %s)",
                    (text, video_url, iteration),
                )
                conn.commit()
            except psycopg2.Error as e:
                print(f"Error inserting into database: {e}")
            finally:
                if cursor:
                    cursor.close()
                self.put_connection(conn)

    def merge_tables(self, table_names: [str]) -> None:
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                add_union_join = lambda x: "UNION ALL" if x != len(table_names) - 1 else ""
                rest_of_query = [
                    f"SELECT text, video_url, iteration, created_at FROM {table} {add_union_join(count)}".strip()
                    for count, table in enumerate(table_names)
                ]
                raw_query = " ".join(rest_of_query)
                cursor.execute(f"INSERT INTO YahooFinance(text, video_url, iteration, created_at) {raw_query}")
                conn.commit()
            except psycopg2.Error as e:
                print(f"Error merging tables: {e}")
            finally:
                if cursor:
                    cursor.close()
                self.put_connection(conn)

    def get_all_entries(self, video_id: str):
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {video_id}")
                return cursor.fetchall()
            except psycopg2.Error as e:
                print(f"Error getting all entries: {e}")
                return []
            finally:
                if cursor:
                    cursor.close()
                self.put_connection(conn)
        return []

if __name__ == "__main__":
    db = DB_MANAGER()
    query = "SELECT * FROM YahooFinance WHERE created_at > NOW() - INTERVAL '5 days'"
    conn = db.get_connection()
    if conn:
      try:
          df = pd.read_sql(query, con=conn)
          df.to_csv("results.csv", index=False)
          last_3_rows = "\n".join(df.tail(3)["text"])
          print(last_3_rows)
      except psycopg2.Error as e:
          print(f"Error executing query: {e}")
      finally:
          db.put_connection(conn)
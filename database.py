#
import mysql.connector
from mysql.connector import pooling, PoolError 
import os

class DB_MANAGER:
    def __init__(self, pool_size = 5):
        self.connection_pool = DB_MANAGER.create_connection_pool(pool_size)

    @staticmethod
    def connect_to_db():
        # read database credentials from environment variables
        db_host = os.environ.get("DB_HOST")
        db_user = os.environ.get("DB_USER")
        db_pass = os.environ.get("DB_PASSWORD")
        db_name = os.environ.get("DB_NAME")
        return mysql.connector.connect(
            user=db_user, password=db_pass, host=db_host, database=db_name
        )

    @staticmethod
    def create_tables(video_id: str):
        db = DB_MANAGER.connect_to_db()
        # create table with | id | text | video_url | iteration | created_at
        cursor = db.cursor()
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {video_id} (id INT AUTO_INCREMENT PRIMARY KEY, text TEXT, video_url VARCHAR(255), iteration INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        )
        db.commit()
        db.close()

    @staticmethod
    def clear_table(video_id: str):
        db = DB_MANAGER.connect_to_db()
        cursor = db.cursor()
        cursor.execute(f"DROP TABLE {video_id}")
        db.commit()
        db.close()

    @staticmethod
    def create_connection_pool(pool_size: int  = 5):
        # read database credentials from environment variables
        db_host = os.environ.get("DB_HOST")
        db_user = os.environ.get("DB_USER")
        db_pass = os.environ.get("DB_PASSWORD")
        db_name = os.environ.get("DB_NAME")
        return pooling.MySQLConnectionPool(
            pool_name="transcript_pool",
            pool_size=pool_size,
            pool_reset_session=True,
            user=db_user,
            password=db_pass,
            host=db_host,
            database=db_name,
        )

    def get_connection_pool(self):
        return self.connection_pool

    def insert_into_db(self, video_id: str, text: str, video_url: str, iteration: int = 0):
        try:
            pool = self.connection_pool
            db = pool.get_connection()
            cursor = db.cursor()
            cursor.execute(
                f"INSERT INTO {video_id} (text, video_url, iteration) VALUES (%s, %s, %s)",
                (text, video_url, iteration),
            )
            db.commit()
            db.close()
        except PoolError  as e:
            print(e)
        except Exception as e:
            print(e)
            print("Error inserting into database")
            # single insert, no need to rollbacks


if __name__ == "__main__":
    DB_MANAGER.create_tables("sample")
    DB_MANAGER.clear_table("sample")
    # clear_table("sample")
    # main()

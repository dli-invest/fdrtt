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
        # replace TL-PSukZktA with underline
        fixed_id = video_id.replace("-", "_")
        cursor = db.cursor()
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {fixed_id} (id INT AUTO_INCREMENT PRIMARY KEY, text TEXT, video_url VARCHAR(255), iteration INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
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

    def merge_tables(self, table_names: [str])->None:
        """
            INSERT INTO Amide_actives_decoys(Structure, Name, Active)
            SELECT * FROM Amide_decoys 
            UNION ALL
            SELECT * FROM Amide_actives; 

            https://stackoverflow.com/questions/26750410/merge-2-tables-in-sql-and-save-into-1-new-table
        """
        try:
            pool = self.connection_pool
            db = pool.get_connection()
            cursor = db.cursor()
            # merge tables 21X5lGlDOfg ACRlRB9k0Bs KWMqeJiIiMo TL_PSukZktA Tiumqeeg92w tde_pFZUoPk tmhI10y8XmI wl1p_H6ckt4
            # I know SQL injection bad but this is only used by me and not for work purposes
            # please do not judge me please and thank you
            add_union_join = lambda x: x != len(table_names) - 1 and "UNION ALL" or ""
            rest_of_query = [f"SELECT text, video_url, iteration, created_at FROM {table} {add_union_join(count)}".strip() for count, table in enumerate(table_names)]
            raw_query = " ".join(rest_of_query)
            cursor.execute(f"INSERT INTO YahooFinance(text, video_url, iteration, created_at) {raw_query}")
        except Exception as e:
            print(e)
            print("Error merging tables")
            return None
        
    def get_all_entries(self, video_id: str):
        try:
            pool = self.connection_pool
            db = pool.get_connection()
            cursor = db.cursor()
            cursor.execute(f"SELECT * FROM {video_id}")
            return cursor
        except Exception as e:
            print(e)
            print("Error getting all entries")
            return []


if __name__ == "__main__":
    # pass 
    # db.merge_tables(table_names=["21X5lGlDOfg", "ACRlRB9k0Bs", "KWMqeJiIiMo", "TL_PSukZktA", "Tiumqeeg92w", "tde_pFZUoPk", "tmhI10y8XmI", "wl1p_H6ckt4"])
    import pandas as pd
    # results = DB_MANAGER().get_all_entries("YahooFinance")
    # # find all results from dp8PhLsUcFE within the last 2 days
    query = "SELECT * FROM YahooFinance WHERE created_at > DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 5 DAY)"
    df = pd.read_sql(query, con=DB_MANAGER.connect_to_db())
    df.to_csv("results.csv", index=False)
    last_3_rows = "\n".join(df.tail(3)["text"])
    print(last_3_rows)
    # clear_table("sample")
    # main()

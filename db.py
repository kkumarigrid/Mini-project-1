import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from dotenv import load_dotenv
import os

load_dotenv()

class Database:

    def __init__(self):
        self.host     = os.getenv("DB_HOST")
        self.name     = os.getenv("DB_NAME")
        self.user     = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port     = os.getenv("DB_PORT")

    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            database=self.name,
            user=self.user,
            password=self.password,
            port=self.port
        )

    @contextmanager
    def get_cursor(self):
        conn = self.get_connection()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

db = Database()

def get_connection():
    return db.get_connection()

import os
import sqlite3
from config import DB_PATH

_test_conn = None

def get_db_connection():
    if os.getenv("TEST_MODE") == "true":
        if _test_conn is None:
            raise Exception("Test mode is enabled but no test DB connection is set.")
        print("Using IN-MEMORY DB for testing")
        return _test_conn
    else:
        print(f"Using REAL DB at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

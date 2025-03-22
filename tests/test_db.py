import os
import sqlite3
import pytest
from config import DB_PATH
import api.db as db_module

@pytest.fixture(scope="function")
def test_db():
    os.environ["TEST_MODE"] = "true"

    mem_conn = sqlite3.connect(":memory:")
    mem_conn.row_factory = sqlite3.Row

    db_module._test_conn = mem_conn

    mem_conn.execute("PRAGMA foreign_keys = OFF;")

    real_conn = sqlite3.connect(DB_PATH)
    real_conn.row_factory = sqlite3.Row

    try:
        cursor = real_conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        schemas = [row[0] for row in cursor.fetchall() if row[0]]
        for schema in schemas:
            mem_conn.execute(schema)

        ordered_tables = [
            "Users", "Categories", "Auctions", "Messages", "Log",
            "Bids", "LikesDislikes", "AutoBidding"
        ]

        for table in ordered_tables:
            rows = real_conn.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                continue
            columns = [desc[1] for desc in real_conn.execute(f"PRAGMA table_info({table});").fetchall()]
            placeholders = ", ".join(["?"] * len(columns))
            col_names = ", ".join(columns)
            mem_conn.executemany(
                f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})",
                [tuple(row[col] for col in columns) for row in rows]
            )

        try:
            seq_rows = real_conn.execute("SELECT * FROM sqlite_sequence").fetchall()
            for row in seq_rows:
                mem_conn.execute("INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)", (row["name"], row["seq"]))
        except sqlite3.Error:
            pass

        mem_conn.commit()
    finally:
        real_conn.close()

    mem_conn.execute("PRAGMA foreign_keys = ON;")

    yield mem_conn

    mem_conn.close()
    db_module._test_conn = None
    os.environ["TEST_MODE"] = "false"

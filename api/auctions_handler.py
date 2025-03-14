import sqlite3
from config import DB_PATH

from .db import get_db_connection
from datetime import datetime

def get_all_auctions(limit=None, include_canceled=False):
    """
    Fetch all auctions with an optional limit and canceled filter.
    """
    try:
        with get_db_connection() as conn:
            query = """
                SELECT a.id, a.title, a.description, a.starting_bid, a.end_datetime,
                       a.start_datetime, a.category_id, c.name AS category_name, 
                       a.created_by, a.created_at, a.canceled
                FROM Auctions a
                LEFT JOIN Categories c ON a.category_id = c.id
                WHERE (:include_canceled OR a.canceled = 0)
                ORDER BY a.start_datetime ASC
            """
            params = {"include_canceled": include_canceled}
            if limit:
                query += " LIMIT :limit"
                params["limit"] = limit
            auctions = conn.execute(query, params).fetchall()
            return [dict(row) for row in auctions]
    except sqlite3.Error as e:
        raise Exception(f"Database error in get_all_auctions: {e}")

def get_auction_by_id(auction_id):
    """
    Fetch a single auction by its ID.
    """
    try:
        with get_db_connection() as conn:
            query = "SELECT * FROM Auctions WHERE id = ?"
            auction = conn.execute(query, (auction_id,)).fetchone()
            return auction

    except sqlite3.Error as e:
        print(f"Database error in get_auction_by_id: {e}")
        return None
    
def insert_auction(title, description, starting_bid, category_id, start_datetime, end_datetime, created_by):
    with get_db_connection() as conn:
        conn.execute(
            '''
            INSERT INTO Auctions (title, description, starting_bid, category_id, start_datetime, end_datetime, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (title, description, starting_bid, category_id, start_datetime, end_datetime, created_by)
        )
        conn.commit()

def update_auction_in_db(auction_id, title, description, starting_bid, category_id, start_datetime, end_datetime):
    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE Auctions
            SET title = ?, description = ?, starting_bid = ?, category_id = ?, start_datetime = ?, end_datetime = ?
            WHERE id = ?
            """,
            (title, description, starting_bid, category_id, start_datetime, end_datetime, auction_id)
        )
        conn.commit()

def cancel_auction_in_db(auction_id):
    """Mark an auction as canceled in the database."""
    with get_db_connection() as conn:
        conn.execute(
            '''
            UPDATE Auctions
            SET canceled = 1
            WHERE id = ?
            ''',
            (auction_id,)
        )
        conn.commit()

def get_top_auctions(limit=3):
    """
    Fetch the top auctions based on total likes.
    """
    try:
        with get_db_connection() as conn:
            query = """
                SELECT a.id, a.title, a.description, a.starting_bid, 
                       COALESCE(SUM(ld.like_dislike), 0) AS total_likes
                FROM Auctions a
                LEFT JOIN LikesDislikes ld ON a.id = ld.auction_id
                WHERE a.canceled = 0
                GROUP BY a.id
                ORDER BY total_likes DESC, RANDOM()
                LIMIT ?
            """
            auctions = conn.execute(query, (limit,)).fetchall()
            return [dict(auction) for auction in auctions]
    except sqlite3.Error as e:
        print(f"Database error in get_top_auctions: {e}")
        return []

def parse_datetime(date_str):
    """Helper function to parse datetime with multiple possible formats."""
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}")


def is_auction_active(auction_id):
    """Check if an auction is active and not canceled."""
    try:
        with get_db_connection() as conn:
            query = """
                SELECT end_datetime, canceled
                FROM Auctions
                WHERE id = ?
            """
            auction = conn.execute(query, (auction_id,)).fetchone()
            if not auction or auction['canceled'] == 1:
                return False
            end_datetime = parse_datetime(auction['end_datetime'])
            return datetime.now() < end_datetime
    except sqlite3.Error as e:
        raise Exception(f"Database error in is_auction_active: {e}")
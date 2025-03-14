import sqlite3
from datetime import datetime
from config import DB_PATH
from .db import get_db_connection


def get_highest_bid(auction_id):
    """Fetch the highest bid for a given auction."""
    try:
        with get_db_connection() as conn:
            query = """
                SELECT MAX(bid_amount) AS highest_bid
                FROM Bids
                WHERE auction_id = ?
            """
            result = conn.execute(query, (auction_id,)).fetchone()
            return result['highest_bid'] if result['highest_bid'] is not None else None
    except sqlite3.Error as e:
        raise Exception(f"Database error in get_highest_bid: {e}")


def get_all_bids_for_auction(auction_id):
    """Fetch all bids for a specific auction, ordered by amount descending."""
    try:
        with get_db_connection() as conn:
            query = """
                SELECT b.id AS bid_id, b.bid_amount, b.bid_datetime, u.email
                FROM Bids b
                INNER JOIN Users u ON b.user_id = u.id
                WHERE b.auction_id = ?
                ORDER BY b.bid_amount DESC
            """
            bids = conn.execute(query, (auction_id,)).fetchall()
            return [dict(bid) for bid in bids]
    except sqlite3.Error as e:
        raise Exception(f"Database error in get_all_bids_for_auction: {e}")

def get_highest_bid_for_auction(auction_id):
    """Fetch the highest bid and corresponding user email for a specific auction."""
    try:
        with get_db_connection() as conn:
            query = """
                SELECT b.bid_amount, u.email
                FROM Bids b
                INNER JOIN Users u ON b.user_id = u.id
                WHERE b.auction_id = ?
                ORDER BY b.bid_amount DESC
                LIMIT 1
            """
            result = conn.execute(query, (auction_id,)).fetchone()
            return {
                "highest_bid": result["bid_amount"],
                "email": result["email"]
            } if result else None
    except sqlite3.Error as e:
        raise Exception(f"Database error in get_highest_bid_for_auction: {e}")


def place_bid(auction_id, user_id, bid_amount):
    """
    Place a manual bid and trigger auto-bidding if applicable.
    """
    with get_db_connection() as conn:
        current_highest_row = conn.execute(
            "SELECT MAX(bid_amount) as highest_bid FROM Bids WHERE auction_id = ?",
            (auction_id,)
        ).fetchone()
        highest_bid = current_highest_row["highest_bid"] or 0

        if bid_amount <= highest_bid:
            return {"success": False, "message": "Your bid must be higher than the current bid."}

        # Insert the manual bid
        conn.execute(
            """
            INSERT INTO Bids (auction_id, user_id, bid_amount, bid_datetime)
            VALUES (?, ?, ?, ?)
            """,
            (auction_id, user_id, bid_amount, datetime.now())
        )
        conn.commit()

        # Trigger auto-bidding logic
        from .auto_bidding_handler import trigger_auto_bidding
        trigger_auto_bidding(auction_id)

        return {"success": True, "message": "Bid placed successfully."}


def delete_bid(bid_id):
    """Delete a bid by its ID."""
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM Bids WHERE id = ?', (bid_id,))
            conn.commit()
            return True
    except sqlite3.Error as e:
        raise Exception(f"Database error in delete_bid: {e}")

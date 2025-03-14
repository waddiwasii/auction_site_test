from .db import get_db_connection
from datetime import datetime

def add_or_update_auto_bid(auction_id, user_id, max_bid, increment=1):
    """
    Add or update an auto-bid for a user in a specific auction.
    """
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM AutoBidding WHERE auction_id = ? AND user_id = ?",
            (auction_id, user_id)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE AutoBidding
                SET max_bid = ?, increment = ?
                WHERE auction_id = ? AND user_id = ?
                """,
                (max_bid, increment, auction_id, user_id)
            )
        else:
            conn.execute(
                """
                INSERT INTO AutoBidding (auction_id, user_id, max_bid, increment)
                VALUES (?, ?, ?, ?)
                """,
                (auction_id, user_id, max_bid, increment)
            )
        conn.commit()
        trigger_auto_bidding(auction_id)


def trigger_auto_bidding(auction_id):
    """
    Handles auto-bidding for an auction based on the highest and next-highest auto-bids.
    """
    with get_db_connection() as conn:
        # Step 1: Fetch all autobids for the auction
        auto_bidders = conn.execute(
            """
            SELECT user_id, max_bid, increment
            FROM AutoBidding
            WHERE auction_id = ?
            ORDER BY max_bid DESC
            """,
            (auction_id,)
        ).fetchall()

        if not auto_bidders:
            return  # No autobidders present, no action needed.

        # Step 2: Get the current highest bid and the user who placed it
        current_bid_row = conn.execute(
            """
            SELECT user_id, MAX(bid_amount) AS highest_bid
            FROM Bids
            WHERE auction_id = ?
            """,
            (auction_id,)
        ).fetchone()
        current_highest_bid = current_bid_row["highest_bid"] or 0
        current_leader_id = current_bid_row["user_id"]

        # Step 3: Filter autobids above the current bid
        valid_bidders = [bidder for bidder in auto_bidders if bidder["max_bid"] > current_highest_bid]
        if len(valid_bidders) == 0:
            return  # No valid autobidders to proceed with.

        # Step 4: Determine the top two bidders
        top_bidder = valid_bidders[0]  # Highest autobid
        next_highest_bidder = valid_bidders[1] if len(valid_bidders) > 1 else None  # Second highest autobid

        # Step 5: Calculate the winning bid
        if next_highest_bidder:
            # If there's a second-highest autobid, calculate the bid just above it
            new_bid = min(top_bidder["max_bid"], next_highest_bidder["max_bid"] + next_highest_bidder["increment"])
        else:
            # No competition, just increment above the current highest bid
            new_bid = min(top_bidder["max_bid"], current_highest_bid + top_bidder["increment"])

        # Step 6: Ensure the bid is valid and higher than the current bid
        if new_bid > current_highest_bid:
            conn.execute(
                """
                INSERT INTO Bids (auction_id, user_id, bid_amount, bid_datetime)
                VALUES (?, ?, ?, ?)
                """,
                (auction_id, top_bidder["user_id"], new_bid, datetime.now())
            )
            conn.commit()


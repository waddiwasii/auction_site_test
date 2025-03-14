from .db import get_db_connection

# CREATE or UPDATE
def add_like_dislike(user_id, auction_id, like_dislike):
    """
    Adds or updates a like/dislike for the given user and auction.
    """
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM LikesDislikes WHERE user_id = ? AND auction_id = ?",
            (user_id, auction_id)
        ).fetchone()

        if existing:
            # Update the like_dislike value if the record exists
            conn.execute(
                "UPDATE LikesDislikes SET like_dislike = ? WHERE id = ?",
                (like_dislike, existing['id'])
            )
        else:
            # Insert a new like_dislike record
            conn.execute(
                "INSERT INTO LikesDislikes (user_id, auction_id, like_dislike) VALUES (?, ?, ?)",
                (user_id, auction_id, like_dislike)
            )
        conn.commit()

# READ
def get_likes_dislikes(auction_id):
    """
    Fetches the total likes and dislikes for an auction.
    """
    with get_db_connection() as conn:
        # Count likes
        likes = conn.execute(
            "SELECT COUNT(*) as count FROM LikesDislikes WHERE auction_id = ? AND like_dislike = 1",
            (auction_id,)
        ).fetchone()['count']

        # Count dislikes
        dislikes = conn.execute(
            "SELECT COUNT(*) as count FROM LikesDislikes WHERE auction_id = ? AND like_dislike = -1",
            (auction_id,)
        ).fetchone()['count']

    return {"likes": likes, "dislikes": dislikes}

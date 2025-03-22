from api.likedislike_handler import add_like_dislike, get_likes_dislikes
from api.user_handler import create_user
from tests.test_db import test_db


def test_add_like_increases_count(test_db):
    """Adding a like should increase the like count by 1 for that auction."""
    _ = test_db
    auction_id = 2
    user_id = 1

    before = get_likes_dislikes(auction_id)
    add_like_dislike(user_id, auction_id, 1)
    after = get_likes_dislikes(auction_id)

    assert after["likes"] == before["likes"] + 1
    assert after["dislikes"] == before["dislikes"]


def test_add_dislike_increases_count(test_db):
    """Adding a dislike should increase the dislike count by 1 for that auction."""
    _ = test_db
    auction_id = 2
    user_id = 2

    before = get_likes_dislikes(auction_id)
    add_like_dislike(user_id, auction_id, -1)
    after = get_likes_dislikes(auction_id)

    assert after["dislikes"] == before["dislikes"] + 1
    assert after["likes"] == before["likes"]


def test_like_overwrites_dislike(test_db):
    """If a user dislikes an item and then likes it, counts should update correctly."""
    _ = test_db
    auction_id = 2
    user_id = 2

    # Step 1: Dislike
    add_like_dislike(user_id, auction_id, -1)
    mid = get_likes_dislikes(auction_id)

    # Step 2: Like (overwrite)
    add_like_dislike(user_id, auction_id, 1)
    after = get_likes_dislikes(auction_id)

    assert after["likes"] == mid["likes"] + 1
    assert after["dislikes"] == mid["dislikes"] - 1

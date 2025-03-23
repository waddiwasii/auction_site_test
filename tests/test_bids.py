from datetime import datetime
from api.bids_handler import place_bid, get_all_bids_for_auction
from tests.test_db import test_db
import api.db as db_module

def test_place_valid_bid(test_db):
    db_module._test_conn = test_db
    user_id = 1
    auction_id = 3
    bid_amount = 900

    bids_before = get_all_bids_for_auction(auction_id)
    result = place_bid(auction_id, user_id, bid_amount)
    bids_after = get_all_bids_for_auction(auction_id)

    assert result["success"] is True
    assert "successfully" in result["message"].lower()
    assert len(bids_after) == len(bids_before) + 1
    assert any(b["bid_amount"] == bid_amount and b["email"] for b in bids_after)

def test_place_first_bid(test_db):
    db_module._test_conn = test_db
    user_id = 1
    auction_id = 4
    bid_amount = 1000

    bids_before = get_all_bids_for_auction(auction_id)
    assert len(bids_before) == 0

    result = place_bid(auction_id, user_id, bid_amount)
    bids_after = get_all_bids_for_auction(auction_id)

    assert result["success"] is True
    assert len(bids_after) == 1
    assert bids_after[0]["bid_amount"] == bid_amount
    assert bids_after[0]["email"]

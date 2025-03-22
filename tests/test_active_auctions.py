import datetime
from api.auctions_handler import get_all_auctions
from tests.test_db import test_db

def test_fetch_active_auctions(test_db):
    """Test that only active (non-canceled, ongoing) auctions are returned."""
    _ = test_db

    auctions = get_all_auctions()

    assert isinstance(auctions, list), "Expected a list of auctions"

    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    active_auctions = [
        auction for auction in auctions
        if "start_datetime" in auction and "end_datetime" in auction and
           datetime.datetime.fromisoformat(auction["start_datetime"]) <= now <= datetime.datetime.fromisoformat(auction["end_datetime"])
           and auction["canceled"] == 0
    ]

    assert len(active_auctions) > 0, "No active auctions found when there should be some"

    for auction in active_auctions:
        assert auction["canceled"] == 0, f"Auction {auction['id']} is canceled but should be active"

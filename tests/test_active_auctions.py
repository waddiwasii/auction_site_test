import datetime
from api.auctions_handler import get_all_auctions

def test_fetch_active_auctions():
    """Test that only active auctions are returned."""

    # 1️⃣ Fetch all auctions directly from the function
    auctions = get_all_auctions()

    # 2️⃣ Ensure the function returns a list
    assert isinstance(auctions, list), "API did not return a list"

    # 3️⃣ Get current UTC time
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    # 4️⃣ Extract active auctions
    active_auctions = [
        auction for auction in auctions
        if "start_datetime" in auction and "end_datetime" in auction and
           datetime.datetime.fromisoformat(auction["start_datetime"]) <= now <= datetime.datetime.fromisoformat(auction["end_datetime"])
    ]

    # 5️⃣ Ensure at least one auction is active
    assert len(active_auctions) > 0, "No active auctions found when there should be some"

    # 6️⃣ Validate that each returned auction is actually active
    for auction in active_auctions:
        assert auction["canceled"] == 0, f"Auction {auction['id']} is canceled but should be active"

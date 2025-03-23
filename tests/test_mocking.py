from unittest.mock import patch
from api.user_handler import authenticate_user

def test_authenticate_user_fails_with_mocked_none_user():
    with patch("api.user_handler.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = None

        result = authenticate_user("fake@example.com", "somepassword")

        assert result is None

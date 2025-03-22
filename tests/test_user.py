from api.user_handler import create_user, authenticate_user
from tests.test_db import test_db

def test_valid_login_admin_user(test_db):
    """User should be able to log in with correct email and password."""
    _ = test_db
    email = "frida.proschinger@gmail.com"
    password = "abc123"

    user = authenticate_user(email, password)

    assert user is not None, "Valid user was not authenticated"
    assert user["username"] == "Frida"
    assert user["is_admin"] == 1


def test_valid_login_normal_user(test_db):
    """Normal (non-admin) user should also be able to log in."""
    _ = test_db
    email = "sarabohlin93@gmail.com"
    password = "abc123"

    user = authenticate_user(email, password)

    assert user is not None, "Valid user was not authenticated"
    assert user["username"] == "Sara"
    assert user["is_admin"] == 0


def test_invalid_login_wrong_password(test_db):
    """User login should fail if the password is incorrect."""
    _ = test_db
    email = "frida.proschinger@gmail.com"
    password = "wrongpassword"

    user = authenticate_user(email, password)

    assert user is None, "User should not be authenticated with incorrect password"


def test_invalid_login_unknown_email(test_db):
    """User login should fail if the email does not exist."""
    _ = test_db
    email = "nonexistent@example.com"
    password = "abc123"

    user = authenticate_user(email, password)

    assert user is None, "User should not be authenticated with an unknown email"


def test_user_signup_success(test_db):
    """A new user should be able to sign up and be stored in the DB."""
    _ = test_db

    username = "TestUser"
    email = "testuser@example.com"
    password = "securepass123"

    create_user(username, email, password)

    # Try to log in using the new credentials
    user = authenticate_user(email, password)

    assert user is not None, "New user could not be authenticated after signup"
    assert user["username"] == username
    assert user["is_admin"] == 0


def test_user_signup_duplicate_email(test_db):
    """Signup should fail if the email is already used."""
    _ = test_db

    username = "AnotherUser"
    email = "frida.proschinger@gmail.com"  # Already exists
    password = "abc123"

    success, message = create_user(username, email, password)

    assert success is False, "Expected failure when using duplicate email"
    assert "exists" in message.lower()

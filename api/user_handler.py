import sqlite3
from config import DB_PATH  # Import the database path from config.py

from .db import get_db_connection

# CREATE
def create_user(username, email, password_hash, is_admin=False):
    """Insert a new user into the Users table."""
    try:
        with get_db_connection() as conn:
            # Attempt to insert the user into the database
            conn.execute(
                '''
                INSERT INTO Users (username, email, password, is_admin)
                VALUES (?, ?, ?, ?)
                ''',
                (username, email, password_hash, is_admin)
            )
            conn.commit()
            return True, "User created successfully."
    except sqlite3.IntegrityError as e:
        # Handle duplicate entries for username or email
        return False, "Username or email already exists."
    except sqlite3.Error as e:
        # Handle generic database errors
        return False, f"Database error: {e}"


# READ
def get_user_by_id(user_id):
    """Fetch a user by their ID."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user


def get_user_by_email(email):
    """Fetch a user by their email."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user


def get_all_users():
    """Fetch all users."""
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM Users').fetchall()
    conn.close()
    return users


# UPDATE
def update_user(user_id, username=None, email=None, password_hash=None, is_admin=None):
    """
    Update a user's information.
    Any parameter can be left as None to keep the current value.
    """
    conn = get_db_connection()

    # Fetch the current user to determine which fields need updating
    user = get_user_by_id(user_id)
    if not user:
        conn.close()
        return None

    # Use the current value if the parameter is not provided
    updated_username = username if username else user['username']
    updated_email = email if email else user['email']
    updated_password_hash = password_hash if password_hash else user['password_hash']
    updated_is_admin = is_admin if is_admin is not None else user['is_admin']

    # Update the user in the database
    conn.execute(
        '''
        UPDATE Users
        SET username = ?, email = ?, password_hash = ?, is_admin = ?
        WHERE id = ?
        ''',
        (updated_username, updated_email, updated_password_hash, updated_is_admin, user_id)
    )
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)  # Return the updated user


# DELETE
def delete_user(user_id):
    """Delete a user by their ID."""
    conn = get_db_connection()
    conn.execute('DELETE FROM Users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

# USER AUTHENTICATION
def authenticate_user(email, password):
    """Check if the provided email and password match a user in the database."""
    conn = get_db_connection()
    user = conn.execute(
        '''
        SELECT id, username, is_admin 
        FROM Users 
        WHERE email = ? AND password = ?
        ''',
        (email, password)
    ).fetchone()
    conn.close()

    # Return the user as a dictionary or None if not found
    if user:
        return {
            'id': user['id'],
            'username': user['username'],
            'is_admin': user['is_admin']
        }
    return None
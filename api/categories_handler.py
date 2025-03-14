import sqlite3
from config import DB_PATH

from .db import get_db_connection


#region READ
def get_category_by_id(category_id):
    with get_db_connection() as conn:
        category = conn.execute(
            'SELECT * FROM Categories WHERE id = ?', 
            (category_id,)
        ).fetchone()
    return category

def get_all_categories():
    with get_db_connection() as conn:
        categories = conn.execute('SELECT * FROM Categories').fetchall()
    return categories

def get_auction_count_by_category(category_id):
    with get_db_connection() as conn:
        count = conn.execute(
            'SELECT COUNT(*) FROM Auctions WHERE category_id = ?', 
            (category_id,)
        ).fetchone()[0]
    return count

def get_categories_with_auction_count():
    """
    Fetch all categories along with the count of auctions under each category for SQLite.
    """
    with get_db_connection() as conn:
        categories_with_count = conn.execute("""
            SELECT 
                Categories.id AS id,
                Categories.name AS name,
                COUNT(Auctions.id) AS auction_count
            FROM 
                Categories
            LEFT JOIN 
                Auctions ON Categories.id = Auctions.category_id
            GROUP BY 
                Categories.id, Categories.name
            ORDER BY 
                Categories.name ASC
        """).fetchall()
    return categories_with_count

#endregion

#region WRITE
def add_category(name, user_id):
    with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO Categories (name, last_changed_by, last_changed) VALUES (?, ?, CURRENT_TIMESTAMP)', 
            (name, user_id)
        )
        conn.commit()

def update_category(category_id, name, user_id):
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE Categories SET name = ?, last_changed_by = ?, last_changed = CURRENT_TIMESTAMP WHERE id = ?', 
            (name, user_id, category_id)
        )
        conn.commit()

def delete_category(category_id):
    with get_db_connection() as conn:
        conn.execute(
            'DELETE FROM Categories WHERE id = ?', 
            (category_id,)
        )
        conn.commit()

#endregion

#region DELETE

def delete_category_by_id(category_id):
    """
    Delete a category if there are no auctions under it.
    """
    with get_db_connection() as conn:
        auction_count = conn.execute(
            "SELECT COUNT(*) FROM Auctions WHERE category_id = ?", (category_id,)
        ).fetchone()[0]

        if auction_count > 0:
            return False, "Category has auctions and cannot be deleted."

        conn.execute("DELETE FROM Categories WHERE id = ?", (category_id,))
        conn.commit()

    return True, "Category deleted successfully."

#endregion
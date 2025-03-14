from .db import get_db_connection

# CREATE
def create_message(sender_name, sender_email, message):
    with get_db_connection() as conn:
        conn.execute(
            '''
            INSERT INTO Messages (sender_name, sender_email, message)
            VALUES (?, ?, ?)
            ''',
            (sender_name, sender_email, message)
        )
        conn.commit()

# READ
def get_all_messages():
    """Fetch all messages."""
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM Messages').fetchall()
    conn.close()
    return messages

def get_message_by_id(message_id):
    """Fetch a single message by its ID."""
    conn = get_db_connection()
    message = conn.execute('SELECT * FROM Messages WHERE id = ?', (message_id,)).fetchone()
    conn.close()
    return message

# UPDATE
def mark_message_as_responded(message_id, responded_by_user_id):
    """Mark a message as responded and log the responder."""
    conn = get_db_connection()
    conn.execute(
        '''
        UPDATE Messages
        SET status = 'Responded', responded_at = CURRENT_TIMESTAMP, responded_by = ?
        WHERE id = ?
        ''',
        (responded_by_user_id, message_id)
    )
    conn.commit()
    conn.close()

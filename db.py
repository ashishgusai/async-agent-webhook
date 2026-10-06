import sqlite3

def get_connection():
    conn = sqlite3.connect("tickets.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                customer_name TEXT,
                issue_description TEXT,
                status TEXT,
                draft TEXT,
                iterations INTEGER
            )
        ''')

def insert_ticket(ticket_id, name, issue):
    with get_connection() as conn:
        conn.execute('''
            INSERT INTO tickets (ticket_id, customer_name, issue_description, status)
            VALUES (?, ?, ?, 'processing')
        ''', (ticket_id, name, issue))

def update_ticket_resolution(ticket_id, draft, iterations):
    with get_connection() as conn:
        conn.execute('''
            UPDATE tickets 
            SET status = 'resolved', draft = ?, iterations = ?
            WHERE ticket_id = ?
        ''', (draft, iterations, ticket_id))

def get_ticket(ticket_id):
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
        return cur.fetchone()
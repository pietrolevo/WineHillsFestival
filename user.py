# file: user.py         author: Pietro Alberto Levo           id: s311516 
# Questo file contiene tutte le funzioni di base per le chiamate al database necessarie agli user

import sqlite3
from werkzeug.security import generate_password_hash

# Connessione al db
def get_connection():
    conn = sqlite3.connect("db/festival.db")
    conn.row_factory = sqlite3.Row
    return conn

# creazione utente e hashing password
def create_user(email, password, role):
    conn = get_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    query = "INSERT INTO users (email, password, role) VALUES (?, ?, ?)"
    cursor.execute(query, (email, hashed_password, role))
    conn.commit()
    conn.close()

# cerca nel db un determinato utente data la email
def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE email = ?"
    cursor.execute(query, (email,))
    user_row = cursor.fetchone()
    conn.close()
    return user_row

# cerca nel db un determinato utente dato l'id
def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))
    user_row = cursor.fetchone()
    conn.close()
    return user_row

# per il numero di partecipanti
def get_total_participants():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT COUNT(DISTINCT user_id) AS total
        FROM tickets
    """
    cursor.execute(query)
    total_participants = cursor.fetchone()["total"]
    conn.close()
    return total_participants



# file: ticket.py         author: Pietro Alberto Levo     id: s311516 
# Questo file contiene tutte le funzioni di base per le chiamate al database necessarie alla gestione dei ticket

import sqlite3

TICKET_PRICES = {
    "Giornaliero": 105.99,
    "Pass 2 Giorni": 200.99,
    "Full Pass": 300.99
}

# connessione al db
def get_connection():
    conn = sqlite3.connect("db/festival.db")
    conn.row_factory = sqlite3.Row
    return conn

# creazione di un ticket e associazione all'acquirente
def create_ticket(user_id, ticket_type, valid_days):
    conn = get_connection()
    cursor = conn.cursor()
    price = TICKET_PRICES.get(ticket_type, 0)
    query = "INSERT INTO tickets (user_id, ticket_type, valid_days, price) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (user_id, ticket_type, valid_days, price))
    conn.commit()
    conn.close()

# ricerca nel db un ticket dato l'user
def get_ticket_by_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM tickets WHERE user_id = ?"
    cursor.execute(query, (user_id,))
    ticket = cursor.fetchone()
    conn.close()
    return ticket

# conta dei tickets venduti per giorni
def count_tickets_for_day(day):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM tickets WHERE valid_days LIKE ?"
    pattern = "%" + day + "%"
    cursor.execute(query, (pattern,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# conta dei tickets per tipologia 
def count_tickets_by_type(ticket_type):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM tickets WHERE ticket_type = ?"
    cursor.execute(query, (ticket_type,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


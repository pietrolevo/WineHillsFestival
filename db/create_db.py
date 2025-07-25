import sqlite3

conn = sqlite3.connect("festival.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('partecipante', 'organizzatore'))
)
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS performances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_name TEXT NOT NULL,
    performance_day TEXT NOT NULL CHECK(performance_day IN ('venerdì', 'sabato', 'domenica')),
    start_time TEXT NOT NULL,
    duration INTEGER NOT NULL,
    description TEXT NOT NULL,
    stage TEXT NOT NULL,
    genre TEXT NOT NULL,
    image_path TEXT NOT NULL,
    published INTEGER NOT NULL DEFAULT 0,
    organizer_id INTEGER
)
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticket_type TEXT NOT NULL CHECK(ticket_type IN ('Giornaliero', 'Pass 2 Giorni', 'Full Pass')),
    valid_days TEXT NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    UNIQUE(user_id)
)
""")
conn.commit()


conn.close()

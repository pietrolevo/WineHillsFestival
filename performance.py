# file: performance.py         author: Pietro Alberto Levo          id: s311516 
# Questo file contiene tutte le funzioni di base per le chiamate al database necessarie alla gestione delle performance

from datetime import datetime, timedelta
import sqlite3

# connessione dal db
def get_connection():
    conn = sqlite3.connect("db/festival.db")
    conn.row_factory = sqlite3.Row
    return conn

# creazione della performance(come bozza) e registrazione nel db
def create_performance(artist_name, performance_day, start_time, duration, description, stage, genre, image_path, published=0, organizer_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    genre = genre.capitalize()
    query = """
    INSERT INTO performances 
    (artist_name, performance_day, start_time, duration, description, stage, genre, image_path, published, organizer_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (artist_name, performance_day, start_time, duration, description, stage, genre, image_path, published, organizer_id))
    conn.commit()
    conn.close()

# cerca nel db un artista per nome per garantire poi unicità
def artist_exists(artist_name):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM performances WHERE artist_name = ?"
    cursor.execute(query, (artist_name,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# prende tutte le performance dal dbs
def get_all_performance():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT * FROM performances
    ORDER BY 
      CASE performance_day
        WHEN 'venerdì' THEN 1
        WHEN 'sabato' THEN 2
        WHEN 'domenica' THEN 3
        ELSE 4
      END,
      start_time ASC
    """
    cursor.execute(query)
    performances = cursor.fetchall()
    conn.close()
    return performances

# trova le performance pubblicate
def get_published_performances():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM performances WHERE published = 1 ORDER BY performance_day, start_time ASC"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

# trova le performance create da un user(tutte)
def get_performances_by_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM performances WHERE organizer_id = ? ORDER BY performance_day, start_time ASC"
    cursor.execute(query, (user_id,))
    performance_list = cursor.fetchall()
    conn.close()
    return performance_list

# trova le performance tramite id
def get_performance_by_id(performance_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM performances WHERE id = ?"
    cursor.execute(query, (performance_id,))
    performance = cursor.fetchone()
    conn.close()
    return performance

# funzione di update del database per aggiornare le performance 
def update_performance(performance_id, artist_name, performance_day, start_time, duration, description, stage, genre, image_path):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    UPDATE performances 
    SET artist_name = ?, performance_day = ?, start_time = ?, duration = ?, description = ?, 
        stage = ?, genre = ?, image_path = ?
    WHERE id = ?
    """
    cursor.execute(query, (artist_name, performance_day, start_time, duration, description, stage, genre, image_path, performance_id))
    conn.commit()
    conn.close()

# pubblicazione performance
def publish_performance(performance_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "UPDATE performances SET published = 1 WHERE id = ?"
    cursor.execute(query, (performance_id,))
    conn.commit()
    conn.close()

# elimina performance (solo se bozza)
def delete_performance(performance_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT published FROM performances WHERE id = ?"
    cursor.execute(query, (performance_id,))
    perf = cursor.fetchone()
    
    if perf and perf["published"] == 0: 
        query = "DELETE FROM performances WHERE id = ?"
        cursor.execute(query, (performance_id,))
        conn.commit()
    
    conn.close()

# controlla se ci sono performance in overlap
def check_overlapping_performance(performance_day, start_time, duration, stage):
    new_start = datetime.strptime(start_time, "%H:%M")
    new_end = new_start + timedelta(minutes=duration)
    
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT start_time, duration FROM performances WHERE performance_day = ? AND stage = ? AND published = 1"
    cursor.execute(query, (performance_day, stage))
    performances = cursor.fetchall()
    conn.close()
    
    for perf in performances:
        existing_start = datetime.strptime(perf["start_time"], "%H:%M")
        existing_end = existing_start + timedelta(minutes=perf["duration"])
        
        if (new_start < existing_end) and (new_end > existing_start):
            return True
    return False

# filtro performance per giorno
def get_distinct_days():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT DISTINCT TRIM(LOWER(performance_day)) AS performance_day
    FROM performances
    ORDER BY 
      CASE TRIM(LOWER(performance_day))
        WHEN 'venerdì' THEN 1
        WHEN 'sabato' THEN 2
        WHEN 'domenica' THEN 3
        ELSE 4
      END
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [row["performance_day"].capitalize() for row in rows]

# filtro performance per palco
def get_distinct_stages():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT DISTINCT stage FROM performances ORDER BY stage ASC"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [row["stage"] for row in rows]

# filtro per genere
def get_distinct_genres():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT DISTINCT genre FROM performances ORDER BY genre ASC"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [row["genre"] for row in rows]

# struttura default della home 
def get_filtered_performances(day=None, stage=None, genre=None, organizer_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if organizer_id:
        query = """
        SELECT * FROM performances 
        WHERE (published = 1 OR organizer_id = ?)
        """
        params = [organizer_id]
    else:
        query = """
        SELECT * FROM performances 
        WHERE published = 1
        """
        params = []
    
    if day:
        query += " AND performance_day = ?"
        params.append(day)
    if stage:
        query += " AND stage = ?"
        params.append(stage)
    if genre:
        query += " AND genre = ?"
        params.append(genre)
    
    query += """
    ORDER BY 
      CASE LOWER(performance_day)
        WHEN 'venerdì' THEN 1
        WHEN 'sabato' THEN 2
        WHEN 'domenica' THEN 3
        ELSE 4
      END,
      start_time ASC
    """
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows

# da struttura default della dashboard 
def get_organizer_dashboard_performances(organizer_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT * FROM performances 
    WHERE published = 1 OR (published = 0 AND organizer_id = ?)
    ORDER BY  
      CASE performance_day 
        WHEN 'venerdì' THEN 1 
        WHEN 'sabato' THEN 2 
        WHEN 'domenica' THEN 3 
        ELSE 4 
      END, 
      start_time ASC 
    """ 
    cursor.execute(query, (organizer_id,))
    performances = cursor.fetchall()
    conn.close()
    return performances
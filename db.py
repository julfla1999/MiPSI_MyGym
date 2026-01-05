import sqlite3

class Database:
    def __init__(self, db_path='mygym.db'):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS users
                           (
                               id            INTEGER PRIMARY KEY AUTOINCREMENT,
                               first_name    TEXT        NOT NULL,
                               last_name     TEXT        NOT NULL,
                               email         TEXT UNIQUE NOT NULL,
                               password_hash TEXT        NOT NULL,
                               role          TEXT        NOT NULL CHECK (role IN ('client', 'trainer', 'manager'))
                           )
                           ''')
            conn.commit()

    def add_user(self, first_name, last_name, email, password_hash, role):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO users (first_name, last_name, email, password_hash, role)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (first_name, last_name, email, password_hash, role))
            conn.commit()

    def get_user(self, email):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            return cursor.fetchone()

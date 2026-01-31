import sqlite3


class Database:
    def __init__(self, db_path: str = "mygym.db"):
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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL CHECK (type IN ('group', 'pt')),
                    name TEXT,
                    description TEXT,
                    difficulty_level TEXT,
                    price REAL,
                    trainer_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    duration_min INTEGER NOT NULL,
                    capacity INTEGER NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'CANCELLED')),
                    FOREIGN KEY (trainer_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservations
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    session_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'CANCELLED')),
                    FOREIGN KEY (client_id) REFERENCES users(id),
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            ''')

            conn.commit()

    # użytkownicy
    def add_user(self, first_name, last_name, email, password_hash, role):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO users (first_name, last_name, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (first_name, last_name, email, password_hash, role))
            conn.commit()
            return cur.lastrowid

    def get_user(self, email):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE email = ?', (email,))
            return cur.fetchone()

    def get_user_by_id(self, user_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            return cur.fetchone()

    def update_user(self, user_id, **changes):
        if not changes:
            return False

        fields = ", ".join([f"{k} = ?" for k in changes.keys()])
        values = list(changes.values()) + [user_id]

        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE users SET {fields} WHERE id = ?", values)
            conn.commit()
        return True

    def get_users_by_role(self, role):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, first_name, last_name FROM users WHERE role = ?", (role,))
            return cur.fetchall()

    # sesje
    def add_session(
        self,
        session_type,
        name,
        description,
        difficulty_level,
        price,
        trainer_id,
        start_time,
        duration_min,
        capacity,
        status="ACTIVE",
    ):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO sessions (
                    type, name, description, difficulty_level, price,
                    trainer_id, start_time, duration_min, capacity, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_type, name, description, difficulty_level, price,
                trainer_id, start_time, duration_min, capacity, status
            ))
            conn.commit()
            return cur.lastrowid

    def get_all_sessions(self):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM sessions WHERE status = "ACTIVE"')
            return cur.fetchall()

    def get_session_by_id(self, session_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
            return cur.fetchone()

    def get_sessions_for_trainer(self, trainer_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM sessions WHERE trainer_id = ? AND status = "ACTIVE"', (trainer_id,))
            return cur.fetchall()

    def update_session(self, session_id, **changes):
        if not changes:
            return False

        fields = ", ".join([f"{k} = ?" for k in changes.keys()])
        values = list(changes.values()) + [session_id]

        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE sessions SET {fields} WHERE id = ?", values)
            conn.commit()
        return True

    def cancel_session(self, session_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE sessions SET status = "CANCELLED" WHERE id = ?', (session_id,))
            conn.commit()

    def session_exists(self, name, start_time):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM sessions WHERE name = ? AND start_time = ?", (name, start_time))
            return cur.fetchone() is not None

    # rezerwacje
    def add_reservation(self, client_id, session_id, created_at, status="ACTIVE"):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO reservations (client_id, session_id, created_at, status)
                VALUES (?, ?, ?, ?)
            ''', (client_id, session_id, created_at, status))
            conn.commit()
            return cur.lastrowid

    def get_client_reservation(self, client_id, session_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT id, client_id, session_id, status
                FROM reservations
                WHERE client_id = ? AND session_id = ? AND status = 'ACTIVE'
            ''', (client_id, session_id))
            return cur.fetchone()

    def get_reservation_by_id(self, reservation_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM reservations WHERE id = ?', (reservation_id,))
            return cur.fetchone()

    def update_reservation_status(self, reservation_id, status):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE reservations SET status = ? WHERE id = ?', (status, reservation_id))
            conn.commit()

    def count_active_reservations(self, session_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM reservations WHERE session_id = ? AND status = "ACTIVE"', (session_id,))
            return cur.fetchone()[0]

    def client_has_reservation(self, client_id, session_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT COUNT(*) FROM reservations WHERE client_id = ? AND session_id = ? AND status = "ACTIVE"',
                (client_id, session_id)
            )
            return cur.fetchone()[0] > 0

    def get_client_reservations_with_details(self, client_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT
                    r.id,
                    r.created_at,
                    r.status,
                    s.start_time,
                    s.type,
                    s.name,
                    s.price,
                    s.trainer_id
                FROM reservations r
                JOIN sessions s ON r.session_id = s.id
                WHERE r.client_id = ?
                ORDER BY s.start_time ASC
            ''', (client_id,))
            return cur.fetchall()

    def get_session_participants(self, session_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT u.id, u.first_name, u.last_name, u.email
                FROM reservations r
                JOIN users u ON r.client_id = u.id
                WHERE r.session_id = ? AND r.status = 'ACTIVE'
                ORDER BY u.last_name, u.first_name
            ''', (session_id,))
            return cur.fetchall()

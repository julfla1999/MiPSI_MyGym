from db import Database
from utils import hash_password



def seed_users():
    db = Database()
    db.create_tables()

    initial_users = [
        ('Marian', 'Kowalski', 'marian@mygym', hash_password('manager123'), 'manager'),
        ('Tomasz', 'Tomasz', 'tomasz@mygym', hash_password('trainer123'), 'trainer'),
        ('Kasia', 'Nowak', 'kasia@mygym', hash_password('trainer123'), 'trainer'),
    ]

    for first, last, email, hash_p, role in initial_users:
        existing = db.get_user(email)
        if existing:
            print(f'Użytkownik {email} już istnieje')
            continue

        db.add_user(first, last, email, hash_p, role)
        print(f'Dodano użytkownika: {email}')


if __name__ == '__main__':
    seed_users()

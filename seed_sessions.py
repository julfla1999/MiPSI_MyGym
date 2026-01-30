from db import Database
from datetime import datetime, timedelta


def seed_sessions():
    db = Database()
    db.create_tables()

    trainers = db.get_users_by_role('trainer')
    if not trainers:
        print('No trainers found. Run seed_users.py first.')
        return

    trainer_id = trainers[0][0]

    base_date = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    base_date -= timedelta(days=base_date.weekday())  # Poniedziałek 00:00

    sessions = [
        # Poniedziałek (0)
        {'name': 'Yoga', 'session_type': 'group', 'description': 'Morning yoga flow', 'difficulty_level': 'easy',
         'price': 30, 'duration_min': 60, 'weekday': 0, 'hour': 8},
        {'name': 'Full body workout', 'session_type': 'group', 'description': 'Total body strength',
         'difficulty_level': 'medium', 'price': 35, 'duration_min': 60, 'weekday': 0, 'hour': 10},
        {'name': 'Sztangi', 'session_type': 'group', 'description': 'Barbell strength training',
         'difficulty_level': 'hard', 'price': 40, 'duration_min': 60, 'weekday': 0, 'hour': 18},

        # Wtorek (1)
        {'name': 'Rowery', 'session_type': 'group', 'description': 'Indoor cycling', 'difficulty_level': 'medium',
         'price': 35, 'duration_min': 60, 'weekday': 1, 'hour': 9},
        {'name': 'Stretching', 'session_type': 'group', 'description': 'Mobility and flexibility',
         'difficulty_level': 'easy', 'price': 30, 'duration_min': 60, 'weekday': 1, 'hour': 17},
        {'name': 'Crossfit', 'session_type': 'group', 'description': 'High intensity WOD', 'difficulty_level': 'hard',
         'price': 40, 'duration_min': 60, 'weekday': 1, 'hour': 18},

        # Środa (2)
        {'name': 'Pilates', 'session_type': 'group', 'description': 'Core stability training',
         'difficulty_level': 'medium', 'price': 35, 'duration_min': 60, 'weekday': 2, 'hour': 8},
        {'name': 'Full body workout', 'session_type': 'group', 'description': 'Functional strength',
         'difficulty_level': 'medium', 'price': 35, 'duration_min': 60, 'weekday': 2, 'hour': 12},
        {'name': 'Yoga', 'session_type': 'group', 'description': 'Evening relaxation', 'difficulty_level': 'easy',
         'price': 30, 'duration_min': 60, 'weekday': 2, 'hour': 17},
        {'name': 'Sztangi', 'session_type': 'group', 'description': 'Power lifting basics', 'difficulty_level': 'hard',
         'price': 40, 'duration_min': 60, 'weekday': 2, 'hour': 20},

        # Czwartek (3)
        {'name': 'Rowery', 'session_type': 'group', 'description': 'Endurance cycling', 'difficulty_level': 'medium',
         'price': 35, 'duration_min': 60, 'weekday': 3, 'hour': 9},
        {'name': 'Stretching', 'session_type': 'group', 'description': 'Deep stretch session',
         'difficulty_level': 'easy', 'price': 30, 'duration_min': 60, 'weekday': 3, 'hour': 16},
        {'name': 'Crossfit', 'session_type': 'group', 'description': 'Metabolic conditioning',
         'difficulty_level': 'hard', 'price': 40, 'duration_min': 60, 'weekday': 3, 'hour': 18},

        # Piątek (4)
        {'name': 'Yoga', 'session_type': 'group', 'description': 'Morning yoga', 'difficulty_level': 'easy',
         'price': 30, 'duration_min': 60, 'weekday': 4, 'hour': 8},
        {'name': 'Pilates', 'session_type': 'group', 'description': 'Posture and core', 'difficulty_level': 'medium',
         'price': 35, 'duration_min': 60, 'weekday': 4, 'hour': 11},
        {'name': 'Full body workout', 'session_type': 'group', 'description': 'Strength & cardio mix',
         'difficulty_level': 'medium', 'price': 35, 'duration_min': 60, 'weekday': 4, 'hour': 17},
        {'name': 'Sztangi', 'session_type': 'group', 'description': 'Heavy lifting', 'difficulty_level': 'hard',
         'price': 40, 'duration_min': 60, 'weekday': 4, 'hour': 19},

        # Sobota (5)
        {'name': 'Rowery', 'session_type': 'group', 'description': 'Weekend ride', 'difficulty_level': 'medium',
         'price': 35, 'duration_min': 60, 'weekday': 5, 'hour': 10},
        {'name': 'Crossfit', 'session_type': 'group', 'description': 'Team WOD', 'difficulty_level': 'hard',
         'price': 40, 'duration_min': 60, 'weekday': 5, 'hour': 12},
        {'name': 'Stretching', 'session_type': 'group', 'description': 'Recovery session', 'difficulty_level': 'easy',
         'price': 30, 'duration_min': 60, 'weekday': 5, 'hour': 16},

        # Niedziela(6)
        {'name': 'Yoga', 'session_type': 'group', 'description': 'Slow yoga & breathing', 'difficulty_level': 'easy',
         'price': 30, 'duration_min': 60, 'weekday': 6, 'hour': 10},
        {'name': 'Pilates', 'session_type': 'group', 'description': 'Light core training', 'difficulty_level': 'easy',
         'price': 30, 'duration_min': 60, 'weekday': 6, 'hour': 13},
    ]

    for s in sessions:
        start_time = base_date + timedelta(
            days=s['weekday'],
            hours=s['hour']
        )

        if db.session_exists(s['name'], start_time.isoformat()):
            print(f"Skipped duplicate: {s['name']} {start_time}")
            continue

        db.add_session(
            session_type=s['session_type'],
            name=s['name'],
            description=s['description'],
            difficulty_level=s['difficulty_level'],
            price=s['price'],
            trainer_id=trainer_id,
            start_time=start_time.isoformat(),
            duration_min=s['duration_min'],
            capacity=10
        )

        print(f"Added: {s['name']} {start_time}")

    print('Sessions seeded successfully.')


if __name__ == '__main__':
    seed_sessions()

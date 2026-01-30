from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import List, Optional

from utils import hash_password


# Enumy
class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class ReservationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


# Modele danych
@dataclass
class User:
    user_id: int
    first_name: str
    last_name: str
    email: str
    password_hash: str
    role: str

    def update(self, db, **changes):
        return db.update_user(self.user_id, **changes)


@dataclass
class Client(User):
    def get_reservations(self, db):
        rows = db.get_client_reservations_with_details(self.user_id)
        return rows

    # Przypadek użycia - przegląd harmonogramu
    def view_schedule(self, schedule: "Schedule") -> List["Session"]:
        return schedule.get_sessions()

    # Przypadek użycia - zapis na zajęcia/trening
    def create_reservation(self, session, reservation_service):
        return reservation_service.create_reservation(self, session)

    # Przypadek użycia - anulowanie rezerwacji
    def cancel_reservation(self, reservation_id, reservation_service):
        return reservation_service.cancel_reservation(reservation_id)


@dataclass
class Trainer(User):
    # Przypadek użycia - podgląd sesji
    def view_my_sessions(self, schedule: "Schedule") -> List["Session"]:
        return [s for s in schedule.get_sessions() if s.trainer == self]

    # Przypadek użycia - podgląd listy uczestników
    def view_participants(self, session: "Session") -> List["Client"]:
        return [r.client for r in session.reservations]


@dataclass
class Manager(User):
    # Przypadek użycia - dodanie zajęć do harmonogramu
    def add_session(self, schedule: "Schedule", session: "Session", schedule_service: "ScheduleService") -> None:
        schedule_service.add_session(schedule=schedule, session=session)

    # Przypadek użycia - edycja zajęć
    def edit_session(self, schedule: "Schedule", session_id: int, schedule_service: "ScheduleService",
                     **changes) -> None:
        schedule_service.edit_session(schedule=schedule, session_id=session_id, **changes)

    # Przypadek użycia - usuwanie zajęć
    def remove_session(self, schedule: "Schedule", session_id: int, schedule_service: "ScheduleService") -> None:
        schedule_service.remove_session(schedule=schedule, session_id=session_id)


class UserService:
    def __init__(self, db):
        self.db = db

    def register_client(self, first_name: str, last_name: str, email: str, password: str):
        existing = self.db.get_user(email)
        if existing:
            return False, 'Email zajęty'

        password_hash = hash_password(password)

        self.db.add_user(first_name, last_name, email, password_hash, role='client')

        return True, 'Konto utworzone'

    def login(self, email, password):
        existing = self.db.get_user(email)

        if not existing:
            return False, 'Błędny email lub hasło'

        user_id, first, last, email, stored_hash, role = existing

        if stored_hash != hash_password(password):
            return False, 'Błędny email lub hasło'

        if role == 'client':
            user = Client(user_id, first, last, email, stored_hash, role)
        elif role == 'trainer':
            user = Trainer(user_id, first, last, email, stored_hash, role)
        elif role == 'manager':
            user = Manager(user_id, first, last, email, stored_hash, role)
        else:
            return False, 'Nieznana rola użytkownika'

        return True, user


@dataclass
class GymBranch:
    branch_id: int
    name: str
    address: str
    schedule: "Schedule" = field(default_factory=lambda: Schedule(schedule_id=1))


@dataclass
class Schedule:
    schedule_id: int


@dataclass
class Session:
    session_id: int
    type: str
    trainer_id: int
    start_time: datetime
    duration_min: int
    capacity: int
    status: str


@dataclass
class ClassSession(Session):
    name: str
    description: str
    difficulty_level: str


@dataclass
class PTSession(Session):
    price: float


@dataclass
class Reservation:
    reservation_id: int
    created_at: datetime
    status: ReservationStatus = ReservationStatus.ACTIVE


# Warstwa logiki

class ScheduleService:
    def __init__(self, db):
        self.db = db

    def get_available_slots(self, session_id: int) -> int:
        row = self.db.get_session_by_id(session_id)
        if not row:
            return 0

        capacity = row[9]  # capacity z tabeli sessions
        reserved = self.db.count_active_reservations(session_id)

        return max(0, capacity - reserved)


    def get_sessions_for_date(self, target_date: date):
        rows = self.db.get_all_sessions()
        sessions = []

        for r in rows:
            (
                session_id,
                type_,
                name,
                description,
                difficulty,
                price,
                trainer_id,
                start_time,
                duration,
                capacity,
                status
            ) = r

            dt = datetime.fromisoformat(start_time)
            if dt.date() != target_date:
                continue

            sessions.append({
                'session_id': session_id,
                'type': type_,
                'name': name or 'Zajęcia',
                'trainer_id': trainer_id,
                'start_time': start_time,
                'hour': dt.hour,
                'capacity': capacity
            })

        return sessions

    def get_week_sessions(self, monday: date):
        week = {day: {} for day in range(7)}

        for i in range(7):
            day_date = monday + timedelta(days=i)
            sessions = self.get_sessions_for_date(day_date)

            for s in sessions:
                dt = datetime.fromisoformat(s['start_time'])
                hour = dt.hour

                week[i].setdefault(hour, []).append(s)

        return week





class ReservationService:
    def __init__(self, db):
        self.db = db

    def create_reservation(self, client, session):
        session_id = session['session_id']

        if self.db.client_has_reservation(client.user_id, session_id):
            return False, 'Masz już rezerwację na te zajęcia'

        if self.db.count_active_reservations(session_id) >= session['capacity']:
            return False, 'Brak wolnych miejsc'

        created_at = datetime.now().isoformat()
        self.db.add_reservation(
            client_id=client.user_id,
            session_id=session_id,
            created_at=created_at,
            status='ACTIVE'
        )

        return True, 'Zapisano na zajęcia'

    def is_user_registered(self, user, session_id):
        return self.db.client_has_reservation(user.user_id, session_id)


    def cancel_reservation(self, client, session):
        res = self.db.get_client_reservation(client.user_id, session['session_id'])
        if not res:
            return False, 'Nie masz rezerwacji na te zajęcia'

        reservation_id = res[0]
        self.db.update_reservation_status(reservation_id, 'CANCELLED')
        return True, 'Rezerwacja anulowana'

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
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

    def get_available_slots(self, session_id):
        session = self.db.get_session_by_id(session_id)
        reserved = self.db.count_active_reservations(session_id)
        return session['capacity'] - reserved

    def get_all_sessions(self):
        return self.db.get_all_sessions()

    def get_sessions_by_type(self, type_):
        return self.db.get_sessions_by_type(type_)

    def add_session(self, **data):
        return self.db.add_session(**data)

    def edit_session(self, session_id, **changes):
        return self.db.update_session(session_id, **changes)

    def remove_session(self, session_id):
        return self.db.cancel_session(session_id)

    def get_session(self, session_id):
        return self.db.get_session_by_id(session_id)


class ReservationService:
    def __init__(self, db):
        self.db = db

    def create_reservation(self, client, session):
        active_count = self.db.count_active_reservations(session.session_id)
        if active_count >= session.capacity:
            return False, 'Brak dostępnych miejsc'

        if self.db.client_has_reservation(client.user_id, session.session_id):
            return False, 'Masz już rezerwację na te zajęcia'

        created_at = datetime.now().isoformat()
        reservation_id = self.db.add_reservation(client_id=client.user_id, session_id=session.session_id,
                                                 created_at=created_at, status='ACTIVE')

        reservation = Reservation(reservation_id=reservation_id, created_at=datetime.fromisoformat(created_at),
                                  status=ReservationStatus.ACTIVE)

        return True, reservation

    def cancel_reservation(self, reservation_id):
        self.db.cancel_reservation(reservation_id)
        return True
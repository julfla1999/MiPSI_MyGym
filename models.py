from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any

from utils import hash_password


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class ReservationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


# modele
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
        return db.get_client_reservations_with_details(self.user_id)

    def create_reservation(self, session: Dict[str, Any], reservation_service: "ReservationService"):
        return reservation_service.create_reservation(self, session)

    def cancel_reservation(
        self,
        reservation_service: "ReservationService",
        reservation_id: Optional[int] = None,
        session: Optional[Dict[str, Any]] = None
    ):
        
        if reservation_id is not None:
            return reservation_service.cancel_reservation_by_id(reservation_id)
        if session is not None:
            return reservation_service.cancel_reservation(self, session)
        return False, "Nie podano rezerwacji do anulowania"


@dataclass
class Trainer(User):
    pass


@dataclass
class Manager(User):
    pass


@dataclass
class GymBranch:
    branch_id: int
    name: str
    address: str
    schedule: "Schedule" = field(default_factory=lambda: Schedule(schedule_id=1))


@dataclass
class Schedule:
    schedule_id: int


# serwisy
class UserService:
    def __init__(self, db):
        self.db = db

    def register_client(self, first_name: str, last_name: str, email: str, password: str):
        existing = self.db.get_user(email)
        if existing:
            return False, "Email zajęty"

        password_hash = hash_password(password)
        self.db.add_user(first_name, last_name, email, password_hash, role="client")
        return True, "Konto utworzone"

    def login(self, email, password):
        existing = self.db.get_user(email)
        if not existing:
            return False, "Błędny email lub hasło"

        user_id, first, last, email, stored_hash, role = existing
        if stored_hash != hash_password(password):
            return False, "Błędny email lub hasło"

        if role == "client":
            user = Client(user_id, first, last, email, stored_hash, role)
        elif role == "trainer":
            user = Trainer(user_id, first, last, email, stored_hash, role)
        elif role == "manager":
            user = Manager(user_id, first, last, email, stored_hash, role)
        else:
            return False, "Nieznana rola użytkownika"

        return True, user


class ScheduleService:
    def __init__(self, db):
        self.db = db

    def _row_to_session_dict(self, row) -> Dict[str, Any]:
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
            status,
        ) = row

        dt = datetime.fromisoformat(start_time)
        return {
            "session_id": session_id,
            "type": type_,
            "name": name or "Zajęcia",
            "description": description,
            "difficulty_level": difficulty,
            "price": price,
            "trainer_id": trainer_id,
            "start_time": start_time,
            "duration_min": duration,
            "capacity": capacity,
            "status": status,
            "hour": dt.hour,
            "date": dt.date(),
        }

    def get_available_slots(self, session_id: int) -> int:
        row = self.db.get_session_by_id(session_id)
        if not row:
            return 0

        capacity = row["capacity"] if isinstance(row, dict) else row[9]
        reserved = self.db.count_active_reservations(session_id)
        return max(0, int(capacity) - int(reserved))

    def get_sessions_for_date(self, target_date: date):
        rows = self.db.get_all_sessions()
        sessions = []
        for r in rows:
            s = self._row_to_session_dict(r)
            if s["date"] != target_date:
                continue
            sessions.append(s)
        return sessions

    def get_week_sessions(self, monday: date):
        week = {day: {} for day in range(7)}
        for i in range(7):
            day_date = monday + timedelta(days=i)
            sessions = self.get_sessions_for_date(day_date)
            for s in sessions:
                hour = s["hour"]
                week[i].setdefault(hour, []).append(s)
        return week

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        rows = self.db.get_all_sessions()
        out = []
        for r in rows:
            s = self._row_to_session_dict(r)
            reserved = self.db.count_active_reservations(s["session_id"])
            s["reserved"] = reserved
            s["available"] = max(0, s["capacity"] - reserved)
            out.append(s)
        out.sort(key=lambda x: x["start_time"])
        return out

    # trener
    def get_sessions_for_trainer(self, trainer_id: int) -> List[Dict[str, Any]]:
        rows = self.db.get_sessions_for_trainer(trainer_id)
        out = []
        for r in rows:
            s = self._row_to_session_dict(r)
            reserved = self.db.count_active_reservations(s["session_id"])
            s["reserved"] = reserved
            s["available"] = max(0, s["capacity"] - reserved)
            out.append(s)
        out.sort(key=lambda x: x["start_time"])
        return out

    # manager
    def add_session(
        self,
        session_type: str,
        trainer_id: int,
        start_time: str,
        duration_min: int,
        capacity: int,
        name: str = None,
        description: str = None,
        difficulty_level: str = None,
        price: float = None
    ):
        if not session_type or session_type not in ("group", "pt"):
            return False, "Niepoprawny typ sesji"
        if int(capacity) <= 0 or int(duration_min) <= 0:
            return False, "Pojemność i czas trwania muszą być > 0"
        try:
            datetime.fromisoformat(start_time)
        except Exception:
            return False, "Niepoprawny format daty (użyj YYYY-MM-DD HH:MM:SS)"

        if name and self.db.session_exists(name, start_time):
            return False, "Taka sesja już istnieje"

        self.db.add_session(
            session_type=session_type,
            name=name,
            description=description,
            difficulty_level=difficulty_level,
            price=price,
            trainer_id=trainer_id,
            start_time=start_time,
            duration_min=int(duration_min),
            capacity=int(capacity),
            status=SessionStatus.ACTIVE.value,
        )
        return True, "Dodano sesję"

    def edit_session(self, session_id: int, **changes):
        allowed = {"name", "description", "difficulty_level", "price", "start_time", "duration_min", "capacity"}
        filtered = {k: v for k, v in changes.items() if k in allowed and v is not None and v != ""}

        if "capacity" in filtered:
            filtered["capacity"] = int(filtered["capacity"])
        if "duration_min" in filtered:
            filtered["duration_min"] = int(filtered["duration_min"])

        if not filtered:
            return False, "Brak zmian do zapisania"

        if "start_time" in filtered:
            try:
                datetime.fromisoformat(filtered["start_time"])
            except Exception:
                return False, "Niepoprawny format daty (użyj YYYY-MM-DD HH:MM:SS)"

        ok = self.db.update_session(session_id, **filtered)
        return (True, "Zaktualizowano sesję") if ok else (False, "Nie udało się zaktualizować")

    def remove_session(self, session_id: int):
        self.db.cancel_session(session_id)
        return True, "Sesja anulowana"


from datetime import datetime
from typing import Any, Dict, Optional, Tuple


class ReservationService:

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _extract_session_fields(session: Any) -> Tuple[Optional[int], Optional[int]]:

        if isinstance(session, dict):
            session_id = session.get("session_id")
            capacity = session.get("capacity")
        else:
            session_id = getattr(session, "session_id", None)
            capacity = getattr(session, "capacity", None)

        try:
            session_id = int(session_id) if session_id is not None else None
        except Exception:
            session_id = None

        try:
            capacity = int(capacity) if capacity is not None else None
        except Exception:
            capacity = None

        return session_id, capacity

    @staticmethod
    def _extract_client_id(client: Any) -> Optional[int]:

        cid = getattr(client, "user_id", None)
        if cid is None:
            cid = getattr(client, "id", None)
        try:
            return int(cid) if cid is not None else None
        except Exception:
            return None

    def create_reservation(self, client: Any, session: Any) -> Tuple[bool, str]:
        client_id = self._extract_client_id(client)
        session_id, capacity = self._extract_session_fields(session)

        if client_id is None or session_id is None or capacity is None:
            return False, "Błędne dane sesji"

        # duplikat
        if self.db.client_has_reservation(client_id, session_id):
            return False, "Masz już rezerwację na te zajęcia"

        # brak miejsc
        reserved = self.db.count_active_reservations(session_id)
        if reserved >= capacity:
            return False, "Brak wolnych miejsc"

        created_at = datetime.now().isoformat(sep=" ", timespec="seconds")
        self.db.add_reservation(
            client_id=client_id,
            session_id=session_id,
            created_at=created_at,
            status="ACTIVE",
        )
        return True, "Zapisano na zajęcia"

    def cancel_reservation(self, client: Any, session: Any) -> Tuple[bool, str]:
        client_id = self._extract_client_id(client)
        session_id, _capacity = self._extract_session_fields(session)

        if client_id is None or session_id is None:
            return False, "Błędne dane sesji"

        res = self.db.get_client_reservation(client_id, session_id)
        if not res:
            return False, "Nie masz rezerwacji na te zajęcia"

        reservation_id = res[0]
        self.db.update_reservation_status(reservation_id, "CANCELLED")
        return True, "Rezerwacja anulowana"

    def cancel_reservation_by_id(self, reservation_id: int) -> Tuple[bool, str]:
        try:
            reservation_id = int(reservation_id)
        except Exception:
            return False, "Niepoprawne ID rezerwacji"

        r = self.db.get_reservation_by_id(reservation_id)
        if not r:
            return False, "Nie znaleziono rezerwacji"

        self.db.update_reservation_status(reservation_id, "CANCELLED")
        return True, "Rezerwacja anulowana"

    def get_participants(self, session_id: int):
        
        try:
            session_id = int(session_id)
        except Exception:
            return []
        return self.db.get_session_participants(session_id)


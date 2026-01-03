from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


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

    # Przypadek użycia - logowanie
    def login(self, email: str, password: str) -> bool:
       
        # TODO: weryfikacja danych
        return True

    # Przypadek użycia - wylogowanie
    def logout(self) -> None:
        
        # TODO
        return None

    # Pomocnicza - edycja profilu
    def update_profile(self, first_name: str, last_name: str) -> None:
        
        # TODO
        self.first_name = first_name
        self.last_name = last_name


@dataclass
class Client(User):
    reservations: List[Reservation] = field(default_factory=list)  

    # Przypadek użycia - przegląd harmonogramu
    def view_schedule(self, schedule: "Schedule") -> List["Session"]:
        
        return schedule.get_sessions()

    # Przypadek użycia - zapis na zajęcia/trening
    def create_reservation(self, session: "Session", reservation_service: "ReservationService") -> "Reservation":
        
        return reservation_service.create_reservation(client=self, session=session)

    # Przypadek użycia - anulowanie rezerwacji
    def cancel_reservation(self, reservation: "Reservation", reservation_service: "ReservationService") -> None:
        
        reservation_service.cancel_reservation(reservation)


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
    def edit_session(self, schedule: "Schedule", session_id: int, schedule_service: "ScheduleService", **changes) -> None:
        
        schedule_service.edit_session(schedule=schedule, session_id=session_id, **changes)

    # Przypadek użycia - usuwanie zajęć
    def remove_session(self, schedule: "Schedule", session_id: int, schedule_service: "ScheduleService") -> None:
        
        schedule_service.remove_session(schedule=schedule, session_id=session_id)


@dataclass
class GymBranch:
    branch_id: int
    name: str
    address: str
    schedule: "Schedule" = field(default_factory=lambda: Schedule(schedule_id=1))  


@dataclass
class Schedule:
    schedule_id: int
    sessions: List["Session"] = field(default_factory=list)

    # Dodanie sesji do harmonogramu
    def add_session(self, session: "Session") -> None:
        
        self.sessions.append(session)

    # Usunięcie sesji z harmonogramu
    def remove_session(self, session_id: int) -> None:
        
        self.sessions = [s for s in self.sessions if s.session_id != session_id]

    # Zwrócenie listy sesji
    def get_sessions(self) -> List["Session"]:
        """Zwrócenie listy sesji"""
        return list(self.sessions)


@dataclass
class Session:
    session_id: int
    start_time: datetime
    duration_min: int
    capacity: int
    status: SessionStatus = SessionStatus.ACTIVE

    trainer: Optional[Trainer] = None
    reservations: List["Reservation"] = field(default_factory=list)

    # Liczba aktywnych rezerwacji
    def get_available_slots(self) -> int:
        
        active_count = sum(1 for r in self.reservations if r.status == ReservationStatus.ACTIVE)
        return max(0, self.capacity - active_count)

    # Powiązanie sesja -> rezerwacja
    def attach_reservation(self, reservation: "Reservation") -> None:
        
        self.reservations.append(reservation)


@dataclass
class ClassSession(Session):
    name: str = ""
    description: str = ""
    difficulty_level: str = ""


@dataclass
class PTSession(Session):
    price: float = 0.0


@dataclass
class Reservation:
    reservation_id: int
    created_at: datetime
    status: ReservationStatus = ReservationStatus.ACTIVE

    client: Optional[Client] = None
    session: Optional[Session] = None

    # Powiązanie rezerwacja -> klient i rezerwacja -> sesja
    def link(self, client: Client, session: Session) -> None:
        
        self.client = client
        self.session = session


# Warstwa logiki
class ScheduleService:
    # Przypadek użycia - dodanie zajęć manager
    def add_session(self, schedule: Schedule, session: Session) -> None:
        
        # TODO: walidacja / konflikty w terminach
        schedule.add_session(session)

    # Przypadek użycia - edycja zajęć
    def edit_session(self, schedule: Schedule, session_id: int, **changes) -> None:
        
        # TODO: odnaleźć sesję i zastosować zmiany
        for s in schedule.sessions:
            if s.session_id == session_id:
                for k, v in changes.items():
                    if hasattr(s, k):
                        setattr(s, k, v)
                return

    # Przypadek użycia - usuwanie zajęć
    def remove_session(self, schedule: Schedule, session_id: int) -> None:
        
        schedule.remove_session(session_id)

    # Sprawdzanie konfliktów terminu trenera
    def check_conflicts(self, schedule: Schedule, trainer: Trainer, start_time: datetime, duration_min: int) -> bool:
        
        # TODO: implementacja dokładnego sprawdzania kolizji
        return False


class ReservationService:
    # Przypadek użycia - zapis na zajęcia / rezerwacja treningu
    def create_reservation(self, client: Client, session: Session) -> Reservation:
        
        # Blokowanie zapisu przy braku dostępnych miejsc
        if session.get_available_slots() <= 0:
            raise ValueError("Brak dostępnych miejsc")

        reservation = Reservation(
            reservation_id=self._generate_reservation_id(),  
            created_at=datetime.now(),
            status=ReservationStatus.ACTIVE,
        )

        # Implementacja powiązań między klasami
        reservation.link(client=client, session=session)
        client.reservations.append(reservation)
        session.attach_reservation(reservation)

        return reservation

    # Przypadek użycia - anulowanie rezerwacji
    def cancel_reservation(self, reservation: Reservation) -> None:
        
        reservation.status = ReservationStatus.CANCELLED

    # Generator ID rezerwacji
    def _generate_reservation_id(self) -> int:
        
        return int(datetime.now().timestamp())

import unittest
from unittest.mock import MagicMock

from models import UserService, ScheduleService, ReservationService


class TestUserService(unittest.TestCase):
    def test_register_client_success(self):
        db = MagicMock()
        db.get_user.return_value = None

        service = UserService(db)
        ok, msg = service.register_client("Tomasz", "Nowak", "t@mail.pl", "haslo123")

        self.assertTrue(ok)
        self.assertEqual(msg, "Konto utworzone")
        db.add_user.assert_called_once()

    def test_register_client_email_taken(self):
        db = MagicMock()
        db.get_user.return_value = (1, "Tomasz", "Nowak", "t@mail.pl", "hash", "client")

        service = UserService(db)
        ok, msg = service.register_client("Tomasz", "Nowak", "t@mail.pl", "haslo123")

        self.assertFalse(ok)
        self.assertEqual(msg, "Email zajęty")
        db.add_user.assert_not_called()


class TestScheduleService(unittest.TestCase):
    def test_get_available_slots(self):
        db = MagicMock()
        db.get_session_by_id.return_value = {"capacity": 10}
        db.count_active_reservations.return_value = 3

        service = ScheduleService(db)
        result = service.get_available_slots(1)

        self.assertEqual(result, 7)

    def test_get_available_slots_when_session_missing(self):
        db = MagicMock()
        db.get_session_by_id.return_value = None

        service = ScheduleService(db)
        result = service.get_available_slots(999)

        self.assertEqual(result, 0)


class FakeClient:
    user_id = 1


class FakeSessionObj:
    session_id = 10
    capacity = 5


class TestReservationService(unittest.TestCase):
    def test_create_reservation_no_slots(self):
        db = MagicMock()
        db.client_has_reservation.return_value = False
        db.count_active_reservations.return_value = 5

        service = ReservationService(db)

        session = {"session_id": 10, "capacity": 5}
        ok, msg = service.create_reservation(FakeClient(), session)

        self.assertFalse(ok)
        self.assertEqual(msg, "Brak wolnych miejsc")

    def test_create_reservation_already_exists(self):
        db = MagicMock()
        db.client_has_reservation.return_value = True

        service = ReservationService(db)

        ok, msg = service.create_reservation(FakeClient(), FakeSessionObj())

        self.assertFalse(ok)
        self.assertEqual(msg, "Masz już rezerwację na te zajęcia")

    def test_create_reservation_success(self):
        db = MagicMock()
        db.client_has_reservation.return_value = False
        db.count_active_reservations.return_value = 0
        db.add_reservation.return_value = 123

        service = ReservationService(db)

        ok, msg = service.create_reservation(FakeClient(), {"session_id": 10, "capacity": 5})

        self.assertTrue(ok)
        self.assertEqual(msg, "Zapisano na zajęcia")
        db.add_reservation.assert_called_once()

class TestManagerFeatures(unittest.TestCase):
    def test_manager_add_session_calls_db(self):
        db = MagicMock()

        db.session_exists.return_value = False
        db.add_session.return_value = 1

        service = ScheduleService(db)

        ok, msg = service.add_session(
            session_type="group",
            trainer_id=5,
            start_time="2026-01-31 10:00:00",
            duration_min=60,
            capacity=12,
            name="Joga",
            description="Zajęcia relaksacyjne",
            difficulty_level="easy",
            price=None,
        )

        self.assertTrue(ok)
        self.assertIn("Dodano", msg)

        db.add_session.assert_called_once()


class TestTrainerFeatures(unittest.TestCase):
    def test_trainer_get_sessions_for_trainer_calls_db(self):
        db = MagicMock()

        db.get_sessions_for_trainer.return_value = [
            (1, "group", "Joga", "opis", "easy", None, 7, "2026-01-31 10:00:00", 60, 10, "ACTIVE"),
            (2, "pt", "Trening personalny", "opis", "mid", 150.0, 7, "2026-01-31 12:00:00", 60, 1, "ACTIVE"),
        ]
        db.count_active_reservations.return_value = 0

        service = ScheduleService(db)

        sessions = service.get_sessions_for_trainer(7)

        self.assertEqual(len(sessions), 2)
        db.get_sessions_for_trainer.assert_called_once_with(7)



if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock
from models import UserService, ScheduleService, ReservationService, Reservation, ReservationStatus


class TestUserService(unittest.TestCase):

    def test_register_client_success(self):
        db = MagicMock()
        db.get_user.return_value = None

        service = UserService(db)

        result, msg = service.register_client('Tomasz', 'Nowak', 't@mail.pl', 'haslo123')

        self.assertTrue(result)
        self.assertEqual(msg, 'Konto utworzone')
        db.add_user.assert_called_once()

    def test_register_client_email_taken(self):
        db = MagicMock()
        db.get_user.return_value = ('id', 'Tomasz', 'Nowak', 't@mail.pl', 'hash', 'client')

        service = UserService(db)

        result, msg = service.register_client('Tomasz', 'Nowak', 't@mail.pl', 'haslo123')

        self.assertFalse(result)
        self.assertEqual(msg, 'Email zajęty')
        db.add_user.assert_not_called()


class TestScheduleService(unittest.TestCase):

    def test_get_available_slots(self):
        db = MagicMock()
        db.get_session_by_id.return_value = {'capacity': 10}
        db.count_active_reservations.return_value = 3

        service = ScheduleService(db)

        result = service.get_available_slots(1)

        self.assertEqual(result, 7)


class FakeClient:
    user_id = 1


class FakeSession:
    session_id = 10
    capacity = 5


class TestReservationService(unittest.TestCase):

    def test_create_reservation_no_slots(self):
        db = MagicMock()
        db.count_active_reservations.return_value = 5  # pełno

        service = ReservationService(db)

        result, msg = service.create_reservation(FakeClient(), FakeSession())

        self.assertFalse(result)
        self.assertEqual(msg, 'Brak dostępnych miejsc')

    def test_create_reservation_already_exists(self):
        db = MagicMock()
        db.count_active_reservations.return_value = 1
        db.client_has_reservation.return_value = True

        service = ReservationService(db)

        result, msg = service.create_reservation(FakeClient(), FakeSession())

        self.assertFalse(result)
        self.assertEqual(msg, 'Masz już rezerwację na te zajęcia')

    def test_create_reservation_success(self):
        db = MagicMock()
        db.count_active_reservations.return_value = 0
        db.client_has_reservation.return_value = False
        db.add_reservation.return_value = 123

        service = ReservationService(db)

        result, reservation = service.create_reservation(FakeClient(), FakeSession())

        self.assertTrue(result)
        self.assertEqual(reservation.reservation_id, 123)
        self.assertIsInstance(reservation, Reservation)
        self.assertEqual(reservation.status, ReservationStatus.ACTIVE)
        db.add_reservation.assert_called_once()


if __name__ == '__main__':
    unittest.main()

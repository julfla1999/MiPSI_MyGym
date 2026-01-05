import unittest
from datetime import datetime
from models import (
    ReservationService,
    Session,
    Reservation,
    ReservationStatus,
    Client,
    Trainer,
    Schedule,
)


class TestReservationService(unittest.TestCase):

    def setUp(self):
        self.service = ReservationService()
        self.trainer = Trainer(user_id=1, first_name="Jane", last_name="Kowalski", email="ko.jan@mygym.com",
                               password_hash="xyz")
        self.client = Client(user_id=2, first_name="Anna", last_name="Nowak", email="no.anna@mail.com",
                             password_hash="abc")
        self.session = Session(session_id=101,
                               start_time=datetime(year=2026, month=2, day=1, hour=12, minute=30), duration_min=60,
                               capacity=2, trainer=self.trainer)

    def test_create_reservation(self):
        reservation = self.service.create_reservation(self.client, self.session)
        self.assertEqual(reservation.status, ReservationStatus.ACTIVE)
        self.assertEqual(reservation.client, self.client)
        self.assertEqual(reservation.session, self.session)
        self.assertEqual(len(self.session.reservations), 1)

    def test_create_reservation_no_slots(self):
        for _ in range(self.session.capacity):
            self.service.create_reservation(self.client, self.session)

        with self.assertRaises(ValueError):
            self.service.create_reservation(self.client, self.session)

    def test_cancel_reservation(self):
        reservation = self.service.create_reservation(self.client, self.session)
        self.service.cancel_reservation(reservation)
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)


class TestSchedule(unittest.TestCase):
    def setUp(self):
        self.schedule = Schedule(schedule_id=1)
        self.trainer = Trainer(user_id=1, first_name="Jane", last_name="Kowalski", email="ko.jan@mygym.com",
                               password_hash="xyz")
        self.session1 = Session(session_id=100, start_time=datetime(year=2026, month=2, day=1, hour=12, minute=30),
                                duration_min=60, capacity=5, trainer=self.trainer)
        self.session2 = Session(session_id=200, start_time=datetime(year=2026, month=2, day=2, hour=13, minute=0),
                                duration_min=30, capacity=8, trainer=self.trainer)

    def test_add_session(self):
        self.schedule.add_session(self.session1)
        self.assertIn(self.session1, self.schedule.sessions)
        self.assertEqual(len(self.schedule.sessions), 1)

    def test_remove_session(self):
        self.schedule.add_session(self.session1)
        self.schedule.add_session(self.session2)
        self.schedule.remove_session(session_id=100)
        self.assertNotIn(self.session1, self.schedule.sessions)
        self.assertEqual(len(self.schedule.sessions), 1)

    def test_get_session(self):
        self.schedule.add_session(self.session1)
        self.schedule.add_session(self.session2)
        sessions = self.schedule.get_sessions()
        self.assertEqual(len(sessions), 2)
        self.assertTrue(all(isinstance(s, Session) for s in sessions))


class TestSession(unittest.TestCase):

    def setUp(self):
        self.trainer = Trainer(user_id=1, first_name="Michał", last_name="Nowicki", email="no.michal@mygym.pl",
                               password_hash="hash")
        self.session = Session(session_id=10, start_time=datetime(year=2026, month=2, day=1, hour=12, minute=0),
                               duration_min=60, capacity=3, trainer=self.trainer)
        self.client1 = Client(user_id=2, first_name="Anna", last_name="Kowalska", email="ko.anna@mail.pl",
                              password_hash="abc")
        self.client2 = Client(user_id=3, first_name="Tomasz", last_name="Tomasz", email="to.tomasz@mail.pl",
                              password_hash="def")
        self.client3 = Client(user_id=4, first_name="Ola", last_name="Wiśniewska", email="wi.ola@mail.pl",
                              password_hash="ghi")

    def test_available_slots_initial(self):
        self.assertEqual(self.session.get_available_slots(), 3)

    def test_available_slots_after_reservations(self):
        for i, client in enumerate([self.client1, self.client2]):
            r = Reservation(reservation_id=i + 1, created_at=datetime.now(), client=client, session=self.session)
            self.session.reservations.append(r)

        self.assertEqual(self.session.get_available_slots(), 1)

    def test_available_slots_after_cancellation(self):
        r1 = Reservation(reservation_id=1, created_at=datetime.now(), client=self.client1, session=self.session)
        r2 = Reservation(reservation_id=2, created_at=datetime.now(), client=self.client2, session=self.session)
        r3 = Reservation(reservation_id=3, created_at=datetime.now(), client=self.client3, session=self.session)

        self.session.reservations.extend([r1, r2, r3])
        self.assertEqual(self.session.get_available_slots(), 0)

        r3.status = ReservationStatus.CANCELLED
        self.assertEqual(self.session.get_available_slots(), 1)


if __name__ == '__main__':
    unittest.main()

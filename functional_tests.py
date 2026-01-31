import unittest

from db import Database
from models import UserService, ScheduleService, ReservationService
from utils import hash_password


class TestFunctionalMyGym(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "test.db"
        self.db = Database(self.test_db_path)
        self.db.create_tables()

        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM reservations")
            cur.execute("DELETE FROM sessions")
            cur.execute("DELETE FROM users")
            conn.commit()

        self.user_service = UserService(self.db)
        self.schedule_service = ScheduleService(self.db)
        self.reservation_service = ReservationService(self.db)

        # seed: manager + trainer
        self.db.add_user("Marian", "Kowalski", "marian@mygym", hash_password("manager123"), "manager")
        self.db.add_user("Tomasz", "Trener", "tomasz@mygym", hash_password("trainer123"), "trainer")
        trainer_row = self.db.get_user("tomasz@mygym")
        self.trainer_id = trainer_row[0]

        # sesja do rezerwacji
        self.session_id = self.db.add_session(
            session_type="group",
            name="Joga",
            description="Zajęcia relaksacyjne",
            difficulty_level="easy",
            price=None,
            trainer_id=self.trainer_id,
            start_time="2026-01-31 10:00:00",
            duration_min=60,
            capacity=2,
            status="ACTIVE",
        )

    def tearDown(self):
        pass

    def test_register_client_creates_user_in_db(self):
        ok, msg = self.user_service.register_client(
            first_name="Kasia",
            last_name="Nowak",
            email="kasia@example.com",
            password="abc123",
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "Konto utworzone")

        row = self.db.get_user("kasia@example.com")
        self.assertIsNotNone(row)
        self.assertEqual(row[5], "client")

    def test_login_returns_correct_role_object(self):
        ok, user = self.user_service.login("marian@mygym", "manager123")
        self.assertTrue(ok)
        self.assertEqual(user.role, "manager")

        ok, user = self.user_service.login("tomasz@mygym", "trainer123")
        self.assertTrue(ok)
        self.assertEqual(user.role, "trainer")

    def test_update_user_changes_record(self):
        ok, _ = self.user_service.register_client("Ala", "Kowalska", "ala@example.com", "pass123")
        self.assertTrue(ok)

        ok, user = self.user_service.login("ala@example.com", "pass123")
        self.assertTrue(ok)

        user.update(self.db, first_name="Alicja")
        row = self.db.get_user("ala@example.com")
        self.assertEqual(row[1], "Alicja")

    def test_manager_add_session_creates_session(self):
        ok, msg = self.schedule_service.add_session(
            session_type="group",
            trainer_id=self.trainer_id,
            start_time="2026-02-01 12:00:00",
            duration_min=45,
            capacity=10,
            name="Pilates",
            description="Core & mobility",
            difficulty_level="mid",
            price=None,
        )
        self.assertTrue(ok)
        self.assertIn("Dodano", msg)

        rows = self.db.get_all_sessions()
        names = [r[2] for r in rows]  
        self.assertIn("Pilates", names)

    def test_client_can_create_and_cancel_reservation(self):
        ok, _ = self.user_service.register_client("Ola", "Test", "ola@example.com", "pass123")
        self.assertTrue(ok)
        ok, client = self.user_service.login("ola@example.com", "pass123")
        self.assertTrue(ok)

        session_row = self.db.get_session_by_id(self.session_id)
        capacity = session_row[9]
        session_dict = {"session_id": self.session_id, "capacity": capacity}

        ok, msg = self.reservation_service.create_reservation(client, session_dict)
        self.assertTrue(ok)
        self.assertEqual(msg, "Zapisano na zajęcia")

        res = self.db.get_client_reservation(client.user_id, self.session_id)
        self.assertIsNotNone(res)

        ok, msg = self.reservation_service.cancel_reservation(client, session_dict)
        self.assertTrue(ok)
        self.assertEqual(msg, "Rezerwacja anulowana")

        res2 = self.db.get_client_reservation(client.user_id, self.session_id)
        self.assertIsNone(res2)

    def test_no_slots_prevents_reservation(self):
        def mk_client(i):
            email = f"c{i}@example.com"
            ok, _ = self.user_service.register_client(f"C{i}", "Test", email, "pass123")
            self.assertTrue(ok)
            ok, c = self.user_service.login(email, "pass123")
            self.assertTrue(ok)
            return c

        c1 = mk_client(1)
        c2 = mk_client(2)
        c3 = mk_client(3)

        session_row = self.db.get_session_by_id(self.session_id)
        capacity = session_row[9]
        session_dict = {"session_id": self.session_id, "capacity": capacity}

        ok, _ = self.reservation_service.create_reservation(c1, session_dict)
        self.assertTrue(ok)
        ok, _ = self.reservation_service.create_reservation(c2, session_dict)
        self.assertTrue(ok)

        ok, msg = self.reservation_service.create_reservation(c3, session_dict)
        self.assertFalse(ok)
        self.assertEqual(msg, "Brak wolnych miejsc")


if __name__ == "__main__":
    unittest.main()

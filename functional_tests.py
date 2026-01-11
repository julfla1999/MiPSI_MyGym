import unittest
import sqlite3
from db import Database
from models import Client, UserService
from utils import hash_password


class TestFunctionalUserFlow(unittest.TestCase):

    def setUp(self):
        self.test_db_path = 'test.db'
        self.db = Database(self.test_db_path)
        self.db.create_tables()

        self.service = UserService(self.db)

    def tearDown(self):
        sqlite3.connect(self.test_db_path).close()

    def test_register_user(self):
        success, message = self.service.register_client(
            first_name='Tomasz',
            last_name='Kowalski',
            email='Tomasz@example.com',
            password='haslo123'
        )

        self.assertTrue(success)
        self.assertEqual(message, 'Konto utworzone')

        user = self.db.get_user('Tomasz@example.com')
        self.assertIsNotNone(user)
        self.assertEqual(user[1], 'Tomasz')
        self.assertEqual(user[3], 'Tomasz@example.com')

    def test_login_returns_correct_user(self):
        password_hash = hash_password('haslo123')
        self.db.add_user(
            first_name='Adam',
            last_name='Kowalski',
            email='adam@example.com',
            password_hash=password_hash,
            role='client'
        )

        success, user = self.service.login('adam@example.com', 'haslo123')

        self.assertTrue(success)
        self.assertIsInstance(user, Client)
        self.assertEqual(user.email, 'adam@example.com')
        self.assertEqual(user.first_name, 'Adam')

    def test_update_user_updates_record(self):
        self.service.register_client(
            first_name='Kasia',
            last_name='Zielińska',
            email='kasia@example.com',
            password='abc123'
        )

        success, user = self.service.login('kasia@example.com', 'abc123')
        self.assertTrue(success)

        user.update(self.db, first_name='Katarzyna')

        updated = self.db.get_user('kasia@example.com')
        self.assertEqual(updated[1], 'Katarzyna')

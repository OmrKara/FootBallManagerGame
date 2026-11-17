import unittest
from unittest.mock import patch

from fastapi import HTTPException
from backend.user_store import MemoryUserStore
from backend import auth


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(auth, "user_store", MemoryUserStore()))
        self.enterContext(patch.object(auth, "sessions", {}))
        self.account = auth.Credentials(username="deniz", password="ornek123")

    def test_register_and_login(self):
        user = auth.register(self.account)
        result = auth.login(self.account)

        self.assertEqual(user, {"user_id": 1, "username": "deniz"})
        self.assertEqual(auth.current_user(result["access_token"]), user)

    def test_duplicate_username_rejected(self):
        auth.register(self.account)
        with self.assertRaises(HTTPException) as error:
            auth.register(self.account)
        self.assertEqual(error.exception.status_code, 409)

    def test_wrong_password_rejected(self):
        auth.register(self.account)
        wrong = auth.Credentials(username="deniz", password="yanlis")
        with self.assertRaises(HTTPException) as error:
            auth.login(wrong)
        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(auth.sessions, {})

    def test_logout_only_ends_own_session(self):
        other = auth.Credentials(username="ece", password="ornek456")
        auth.register(self.account)
        other_user = auth.register(other)
        first_token = auth.login(self.account)["access_token"]
        other_token = auth.login(other)["access_token"]

        auth.logout(first_token)

        with self.assertRaises(HTTPException) as error:
            auth.current_user(first_token)
        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(auth.current_user(other_token), other_user)

    def test_new_login_returns_same_user_id_after_logout(self):
        registered = auth.register(self.account)

        first_login = auth.login(self.account)
        auth.logout(first_login["access_token"])

        second_login = auth.login(self.account)
        current = auth.current_user(second_login["access_token"])

        self.assertEqual(current["user_id"], registered["user_id"])
        self.assertEqual(current["username"], registered["username"])
"""Password hashing, the password policy, and the login lockout."""

from __future__ import annotations

import unittest

from cleanhome import config, security
from cleanhome.services import AuthError, auth_service
from cleanhome.tests.base import ServiceTestCase


class PasswordHashingTests(unittest.TestCase):
    """Hashing and verification."""

    def test_hash_and_verify_round_trip(self) -> None:
        salt, digest = security.hash_password("CorrectHorse1")
        self.assertTrue(security.verify_password("CorrectHorse1", salt, digest))

    def test_wrong_password_does_not_verify(self) -> None:
        salt, digest = security.hash_password("CorrectHorse1")
        self.assertFalse(security.verify_password("CorrectHorse2", salt, digest))

    def test_same_password_gets_a_different_hash(self) -> None:
        first_salt, first_digest = security.hash_password("CorrectHorse1")
        second_salt, second_digest = security.hash_password("CorrectHorse1")
        self.assertNotEqual(first_salt, second_salt)
        self.assertNotEqual(first_digest, second_digest)

    def test_missing_salt_or_hash_fails_closed(self) -> None:
        self.assertFalse(security.verify_password("CorrectHorse1", "", "abc"))
        self.assertFalse(security.verify_password("CorrectHorse1", "abc", ""))

    def test_generated_passwords_satisfy_the_policy(self) -> None:
        for _ in range(10):
            self.assertEqual(security.password_problems(security.generate_password()), [])

    def test_password_policy_rejects_short_and_letter_only(self) -> None:
        self.assertTrue(security.password_problems("short"))
        self.assertTrue(security.password_problems("onlylettershere"))
        self.assertEqual(security.password_problems("LongEnough1"), [])


class LockoutTests(ServiceTestCase):
    """Five wrong passwords lock the account for a few minutes."""

    def setUp(self) -> None:
        super().setUp()
        self.email = "lockout@test.ph"
        self.password = "TestPass123"
        self.make_customer(self.email, self.password)

    def test_five_failures_lock_the_account(self) -> None:
        for _ in range(config.MAX_FAILED_LOGINS - 1):
            with self.assertRaises(AuthError):
                auth_service.login(self.email, "WrongPass123")

        # The account still works right up to the last attempt.
        user = auth_service.login(self.email, self.password)
        self.assertEqual(user["email"], self.email)

        # That success reset the counter, so the next five failures lock it.
        for _ in range(config.MAX_FAILED_LOGINS):
            with self.assertRaises(AuthError):
                auth_service.login(self.email, "WrongPass123")

        # Now the correct password is refused too.
        with self.assertRaises(AuthError) as caught:
            auth_service.login(self.email, self.password)
        self.assertIn("too many failed attempts", str(caught.exception).lower())

    def test_successful_login_clears_the_failure_counter(self) -> None:
        for _ in range(2):
            with self.assertRaises(AuthError):
                auth_service.login(self.email, "WrongPass123")
        auth_service.login(self.email, self.password)
        for _ in range(config.MAX_FAILED_LOGINS - 1):
            with self.assertRaises(AuthError):
                auth_service.login(self.email, "WrongPass123")
        user = auth_service.login(self.email, self.password)
        self.assertEqual(user["email"], self.email)

    def test_unknown_email_gives_the_same_message(self) -> None:
        with self.assertRaises(AuthError) as unknown:
            auth_service.login("nobody@test.ph", "Whatever123")
        with self.assertRaises(AuthError) as wrong_password:
            auth_service.login(self.email, "Whatever123")
        self.assertEqual(str(unknown.exception), str(wrong_password.exception))

    def test_inactive_account_cannot_sign_in(self) -> None:
        from cleanhome import db

        db.execute("UPDATE users SET is_active = 0 WHERE email = ?", (self.email,))
        with self.assertRaises(AuthError):
            auth_service.login(self.email, self.password)

    def test_login_gives_the_same_message_for_an_empty_email(self) -> None:
        with self.assertRaises(AuthError) as empty:
            auth_service.login("", self.password)
        self.assertEqual(str(empty.exception), "Incorrect email or password.")


if __name__ == "__main__":
    unittest.main()

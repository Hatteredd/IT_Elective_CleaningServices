"""The command-line administrator password reset tool."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from cleanhome import db, reset_password
from cleanhome.tests.base import ServiceTestCase


class ResetPasswordTests(ServiceTestCase):
    """Resetting a password must also clear the lockout."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("admin@test.ph", "OldPass123")
        self.customer = self.make_customer("customer@test.ph", "OldPass123")

    def _lock(self, email: str) -> None:
        db.execute(
            "UPDATE users SET failed_attempts = 5, locked_until = '2099-01-01 00:00:00', "
            "is_active = 0 WHERE email = ?",
            (email,),
        )

    def _quiet(self, call, *args):
        """Run a function that prints and swallow its output."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = call(*args)
        return result, buffer.getvalue()

    def _state(self, email: str) -> dict:
        row = db.query_one(
            "SELECT is_active, failed_attempts, locked_until FROM users WHERE email = ?",
            (email,),
        )
        return dict(row) if row else {}

    def test_reset_clears_the_lockout_and_reactivates_the_account(self) -> None:
        self._lock("admin@test.ph")
        code, _ = self._quiet(reset_password.reset, "admin@test.ph", "BrandNew123")
        self.assertEqual(code, 0)
        state = self._state("admin@test.ph")
        self.assertEqual(state["failed_attempts"], 0)
        self.assertIsNone(state["locked_until"])
        self.assertEqual(state["is_active"], 1)

    def test_the_new_password_signs_in(self) -> None:
        from cleanhome.services import auth_service

        self._lock("admin@test.ph")
        self._quiet(reset_password.reset, "admin@test.ph", "BrandNew123")
        user = auth_service.login("admin@test.ph", "BrandNew123")
        self.assertEqual(user["role"], "admin")

    def test_an_unknown_email_is_reported(self) -> None:
        code, _ = self._quiet(reset_password.reset, "nobody@test.ph", "BrandNew123")
        self.assertEqual(code, 1)

    def test_a_customer_account_cannot_be_reset(self) -> None:
        code, _ = self._quiet(reset_password.reset, "customer@test.ph", "BrandNew123")
        self.assertEqual(code, 1)

    def test_a_weak_password_is_refused(self) -> None:
        code, _ = self._quiet(reset_password.reset, "admin@test.ph", "short")
        self.assertEqual(code, 1)
        code, _ = self._quiet(reset_password.reset, "admin@test.ph", "nodigitshere")
        self.assertEqual(code, 1)

    def test_list_shows_the_admin_accounts(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = reset_password.list_admins()
        self.assertEqual(code, 0)
        self.assertIn("admin@test.ph", buffer.getvalue())
        self.assertNotIn("customer@test.ph", buffer.getvalue())

    def test_generate_prints_the_password_once(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = reset_password.main(["--email", "admin@test.ph", "--generate"])
        output = buffer.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("New password:", output)
        self.assertIn("Write it down now", output)

    def test_the_password_is_asked_for_twice(self) -> None:
        answers = iter(["Typing123", "Typing123"])
        original = reset_password._ask
        reset_password._ask = lambda prompt: next(answers)
        try:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = reset_password.main(["--email", "admin@test.ph"])
        finally:
            reset_password._ask = original
        self.assertEqual(code, 0)
        self.assertIn("Password reset for admin@test.ph", buffer.getvalue())

    def test_two_different_passwords_change_nothing(self) -> None:
        answers = iter(["Typing123", "Typing456"])
        original = reset_password._ask
        reset_password._ask = lambda prompt: next(answers)
        try:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = reset_password.main(["--email", "admin@test.ph"])
        finally:
            reset_password._ask = original
        self.assertEqual(code, 1)
        self.assertIn("did not match", buffer.getvalue())
        from cleanhome.services import auth_service

        self.assertIsNotNone(auth_service.login("admin@test.ph", "OldPass123"))


if __name__ == "__main__":
    unittest.main()

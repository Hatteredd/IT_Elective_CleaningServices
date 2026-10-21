"""Sign-up validation and the customer administration rules."""

from __future__ import annotations

import unittest

from cleanhome.services import ConflictError, PermissionDenied, ValidationError, auth_service
from cleanhome.tests.base import ServiceTestCase


class RegistrationTests(ServiceTestCase):
    """Every field is checked before the account is created."""

    def register(self, **overrides):
        data = {
            "full_name": "Juan Dela Cruz",
            "email": "juan@example.com",
            "phone": "09171234567",
            "password": "GoodPass123",
            "confirm_password": "GoodPass123",
        }
        data.update(overrides)
        return auth_service.register(**data)

    def test_valid_registration_creates_a_customer(self) -> None:
        user = self.register()
        self.assertEqual(user["role"], "customer")
        self.assertEqual(user["email"], "juan@example.com")
        self.assertTrue(user["is_active"])

    def test_name_is_required(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            self.register(full_name="   ")
        self.assertEqual(caught.exception.field, "full_name")

    def test_email_must_look_like_an_email(self) -> None:
        for bad in ("juan", "juan@", "@example.com", "juan example.com"):
            with self.assertRaises(ValidationError) as caught:
                self.register(email=bad)
            self.assertEqual(caught.exception.field, "email")

    def test_email_is_unique_regardless_of_case(self) -> None:
        self.register(email="juan@example.com")
        with self.assertRaises(ValidationError) as caught:
            self.register(email="JUAN@example.com")
        self.assertEqual(caught.exception.field, "email")

    def test_phone_must_be_a_valid_mobile_number(self) -> None:
        for bad in ("1234", "0917123456", "0917123456789", "0917 123 4567"):
            with self.assertRaises(ValidationError) as caught:
                self.register(phone=bad)
            self.assertEqual(caught.exception.field, "phone")

    def test_phone_accepts_the_international_form(self) -> None:
        user = self.register(phone="+639171234567")
        self.assertEqual(user["phone"], "+639171234567")

    def test_phone_is_optional(self) -> None:
        user = self.register(phone="")
        self.assertEqual(user["role"], "customer")

    def test_password_policy_is_enforced(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            self.register(password="short", confirm_password="short")
        self.assertEqual(caught.exception.field, "password")

    def test_passwords_must_match(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            self.register(confirm_password="Different123")
        self.assertEqual(caught.exception.field, "confirm_password")

    def test_password_is_never_stored_in_plain_text(self) -> None:
        from cleanhome import db

        self.register()
        row = db.query_one("SELECT pw_hash, pw_salt FROM users WHERE email = ?",
                           ("juan@example.com",))
        self.assertNotIn("GoodPass123", row["pw_hash"])
        self.assertNotEqual(row["pw_hash"], row["pw_salt"])


class ProfileTests(ServiceTestCase):
    """Editing a profile and changing a password."""

    def setUp(self) -> None:
        super().setUp()
        self.user = self.make_customer("profile@test.ph", "TestPass123")

    def test_update_profile_saves_the_changes(self) -> None:
        updated = auth_service.update_profile(self.user, "New Name", "09181234567",
                                               "12 Quezon Ave")
        self.assertEqual(updated["full_name"], "New Name")
        self.assertEqual(updated["phone"], "09181234567")
        self.assertEqual(updated["address"], "12 Quezon Ave")

    def test_update_profile_rejects_a_bad_phone(self) -> None:
        with self.assertRaises(ValidationError):
            auth_service.update_profile(self.user, "New Name", "123", "Address")

    def test_change_password_needs_the_current_one(self) -> None:
        with self.assertRaises(ValidationError):
            auth_service.change_password(self.user, "WrongPass123", "NewPass456",
                                         "NewPass456")

    def test_change_password_replaces_the_old_one(self) -> None:
        auth_service.change_password(self.user, "TestPass123", "NewPass456", "NewPass456")
        user = auth_service.find_user_by_email("profile@test.ph")
        self.assertIsNotNone(user)
        auth_service.login("profile@test.ph", "NewPass456")

    def test_change_password_checks_the_confirmation(self) -> None:
        with self.assertRaises(ValidationError):
            auth_service.change_password(self.user, "TestPass123", "NewPass456", "Other123")


class AdminAccountTests(ServiceTestCase):
    """Only an administrator may manage other accounts."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")

    def test_admin_can_create_another_admin(self) -> None:
        created = auth_service.create_admin(self.admin, "Second Admin",
                                            "second@test.ph", "TestPass123")
        self.assertEqual(created["role"], "admin")

    def test_customer_cannot_create_an_admin(self) -> None:
        with self.assertRaises(PermissionDenied):
            auth_service.create_admin(self.customer, "Sneaky", "sneaky@test.ph",
                                      "TestPass123")

    def test_admin_cannot_create_a_duplicate_email(self) -> None:
        with self.assertRaises(ConflictError):
            auth_service.create_admin(self.admin, "Duplicate", "boss@test.ph", "TestPass123")

    def test_customer_cannot_deactivate_an_account(self) -> None:
        with self.assertRaises(PermissionDenied):
            auth_service.set_user_active(self.customer, self.customer["id"], False)

    def test_admin_can_deactivate_and_reactivate(self) -> None:
        auth_service.set_user_active(self.admin, self.customer["id"], False)
        self.assertFalse(auth_service.get_user(self.customer["id"])["is_active"])
        auth_service.set_user_active(self.admin, self.customer["id"], True)
        self.assertTrue(auth_service.get_user(self.customer["id"])["is_active"])

    def test_customer_cannot_list_customers(self) -> None:
        with self.assertRaises(PermissionDenied):
            auth_service.list_customers(self.customer, "")


if __name__ == "__main__":
    unittest.main()

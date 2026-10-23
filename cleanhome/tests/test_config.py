"""Data locations and the company details block."""

from __future__ import annotations

import unittest
from pathlib import Path

from cleanhome import config


class DataDirectoryTests(unittest.TestCase):
    """Source runs stay in the project; a frozen app uses LocalAppData."""

    def test_source_runs_use_the_project_root(self) -> None:
        self.assertEqual(config.resolve_data_dir(False, None), config.PROJECT_DIR)
        self.assertEqual(config.resolve_data_dir(False, "C:/ignored"), config.PROJECT_DIR)

    def test_a_frozen_app_uses_local_app_data(self) -> None:
        folder = config.resolve_data_dir(True, "C:/Users/Test/AppData/Local")
        self.assertEqual(folder, Path("C:/Users/Test/AppData/Local") / "CleanHomePH")

    def test_a_frozen_app_falls_back_to_the_home_folder(self) -> None:
        folder = config.resolve_data_dir(True, None)
        self.assertEqual(folder, Path.home() / "AppData" / "Local" / "CleanHomePH")

    def test_the_backup_folder_lives_under_the_data_folder(self) -> None:
        self.assertEqual(config.BACKUP_DIR, config.DATA_DIR / "backups")
        self.assertEqual(config.DB_PATH.parent, config.DATA_DIR)
        self.assertEqual(config.LOG_PATH.parent, config.DATA_DIR)


class CompanyDetailsTests(unittest.TestCase):
    """The About, Contact, navigation, and footer screens read these."""

    def test_every_company_detail_is_filled_in(self) -> None:
        for name in ("COMPANY_NAME", "COMPANY_TAGLINE", "COMPANY_REGION",
                     "COMPANY_EMAIL", "COMPANY_PHONE", "COMPANY_ADDRESS",
                     "COMPANY_HOURS", "SERVICE_AREAS"):
            value = getattr(config, name)
            self.assertTrue(str(value).strip(), name)

    def test_company_details_are_not_shared_with_the_business_rules(self) -> None:
        self.assertGreater(config.CANCEL_CUTOFF_HOURS, 0)
        self.assertGreater(config.MAX_CONCURRENT_BOOKINGS, 0)


if __name__ == "__main__":
    unittest.main()

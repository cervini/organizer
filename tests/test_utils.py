import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))
import utils


class ConfigStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.user_config = self.root / "user" / "config.yaml"
        self.legacy_config = self.root / "legacy" / "config.yaml"
        self.legacy_config.parent.mkdir()
        self.legacy_config.write_text(
            "interval: 7\nrules:\n- name: Old rule\n  extensions: [.pdf]\n",
            encoding="utf-8",
        )

    def test_config_directory_uses_platform_user_settings_location(self):
        windows_appdata = str(self.root / "AppData" / "Roaming")
        xdg_config = str(self.root / "XDG")
        with (
            patch.object(utils.sys, "platform", "win32"),
            patch.dict(os.environ, {"APPDATA": windows_appdata}),
        ):
            self.assertEqual(
                utils.config_directory(),
                os.path.join(windows_appdata, "Organizer"),
            )
        with (
            patch.object(utils.sys, "platform", "linux"),
            patch.dict(os.environ, {"XDG_CONFIG_HOME": xdg_config}),
        ):
            self.assertEqual(
                utils.config_directory(),
                os.path.join(xdg_config, "organizer"),
            )

    def test_load_migrates_existing_config_to_user_directory(self):
        with (
            patch.object(utils, "get_config_path", return_value=str(self.user_config)),
            patch.object(
                utils,
                "_legacy_config_paths",
                return_value=[str(self.legacy_config)],
            ),
        ):
            config = utils.load_config()

        self.assertEqual(config["interval"], 7)
        self.assertEqual(config["rules"][0]["name"], "Old rule")
        self.assertTrue(self.user_config.is_file())
        self.assertTrue(self.legacy_config.is_file())

    def test_load_migrates_config_from_frozen_installation_directory(self):
        executable_directory = self.root / "installed"
        executable_directory.mkdir()
        installed_config = executable_directory / "config.yaml"
        installed_config.write_text("interval: 9\nrules: []\n", encoding="utf-8")
        bundled_directory = self.root / "bundle"
        bundled_resources = bundled_directory / "resources"
        bundled_resources.mkdir(parents=True)
        (bundled_resources / "config.yaml").write_text(
            "interval: 2\nrules: []\n", encoding="utf-8"
        )

        with (
            patch.object(utils, "get_config_path", return_value=str(self.user_config)),
            patch.object(utils.sys, "frozen", True, create=True),
            patch.object(
                utils.sys,
                "executable",
                str(executable_directory / "main.exe"),
            ),
            patch.object(utils.sys, "_MEIPASS", str(bundled_directory), create=True),
        ):
            config = utils.load_config()

        self.assertEqual(config["interval"], 9)
        self.assertTrue(self.user_config.is_file())

    def test_save_creates_and_writes_user_config(self):
        with patch.object(utils, "get_config_path", return_value=str(self.user_config)):
            utils.save_config({"interval": 3, "rules": []})

        with self.user_config.open(encoding="utf-8") as config_file:
            self.assertEqual(yaml.safe_load(config_file), {"interval": 3, "rules": []})

    def test_load_does_not_replace_existing_user_config_with_legacy_file(self):
        self.user_config.parent.mkdir()
        self.user_config.write_text("interval: 4\nrules: []\n", encoding="utf-8")
        with (
            patch.object(utils, "get_config_path", return_value=str(self.user_config)),
            patch.object(
                utils,
                "_legacy_config_paths",
                return_value=[str(self.legacy_config)],
            ),
        ):
            config = utils.load_config()

        self.assertEqual(config["interval"], 4)


class FileSorterTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.downloads = Path(self.temporary_directory.name) / "Downloads"
        self.downloads.mkdir()

    def run_sorter(self, rules):
        with (
            patch.object(utils, "locate_folder_path", return_value=str(self.downloads)),
            patch.object(utils, "get_rules", return_value=rules),
        ):
            utils.file_sorter()

    def make_rule(self, name, destination, extensions=None, keywords=None):
        return {
            "name": name,
            "destination": destination,
            "extensions": extensions or [],
            "keywords": keywords or [],
            "sub": True,
        }

    def test_extension_match_moves_file_to_first_matching_rule(self):
        first_destination = self.downloads / "Documents"
        second_destination = self.downloads / "Other"
        first_destination.mkdir()
        second_destination.mkdir()
        source = self.downloads / "report.pdf"
        source.write_text("report")

        self.run_sorter(
            [
                self.make_rule("PDFs", "Documents", extensions=[".pdf"]),
                self.make_rule("All files", "Other", extensions=[".pdf"]),
            ]
        )

        self.assertEqual((first_destination / "report.pdf").read_text(), "report")
        self.assertFalse((second_destination / "report.pdf").exists())
        self.assertFalse(source.exists())

    def test_keyword_match_moves_file(self):
        destination = self.downloads / "Invoices"
        destination.mkdir()
        source = self.downloads / "invoice-march.txt"
        source.write_text("invoice")

        self.run_sorter(
            [self.make_rule("Invoices", "Invoices", keywords=["invoice"])]
        )

        self.assertEqual((destination / source.name).read_text(), "invoice")
        self.assertFalse(source.exists())

    def test_duplicate_names_keep_existing_files_and_move_to_next_free_name(self):
        destination = self.downloads / "Documents"
        destination.mkdir()
        (destination / "report.txt").write_text("existing original")
        (destination / "report(1).txt").write_text("existing duplicate")
        downloads_duplicate = self.downloads / "report(1).txt"
        downloads_duplicate.mkdir()
        source = self.downloads / "report.txt"
        source.write_text("new report")

        self.run_sorter(
            [self.make_rule("Text", "Documents", extensions=[".txt"])]
        )

        self.assertEqual((destination / "report.txt").read_text(), "existing original")
        self.assertEqual(
            (destination / "report(1).txt").read_text(), "existing duplicate"
        )
        self.assertEqual((destination / "report(2).txt").read_text(), "new report")
        self.assertTrue(downloads_duplicate.is_dir())
        self.assertFalse(source.exists())
        self.assertEqual(
            {path.name for path in destination.iterdir()},
            {"report.txt", "report(1).txt", "report(2).txt"},
        )

    def test_unmatched_files_are_left_in_downloads(self):
        source = self.downloads / "notes.txt"
        source.write_text("notes")
        destination = self.downloads / "Images"
        destination.mkdir()

        self.run_sorter(
            [self.make_rule("Images", "Images", extensions=[".png"])]
        )

        self.assertTrue(source.exists())
        self.assertEqual(list(destination.iterdir()), [])

    def test_sort_plan_shows_moves_without_changing_files(self):
        destination = self.downloads / "Documents"
        destination.mkdir()
        (destination / "report.pdf").write_text("existing report")
        source = self.downloads / "report.pdf"
        source.write_text("new report")

        plan = utils.get_sort_plan(
            str(self.downloads),
            [self.make_rule("PDFs", "Documents", extensions=[".pdf"])],
        )

        self.assertEqual(
            plan,
            [(str(source), str(destination / "report(1).pdf"))],
        )
        self.assertEqual(source.read_text(), "new report")
        self.assertEqual((destination / "report.pdf").read_text(), "existing report")
        self.assertFalse((destination / "report(1).pdf").exists())

    def test_sort_plan_reserves_names_for_multiple_files(self):
        destination = self.downloads / "Documents"
        destination.mkdir()
        (destination / "report.txt").write_text("existing report")
        first_source = self.downloads / "report.txt"
        second_source = self.downloads / "report(1).txt"
        first_source.write_text("first new report")
        second_source.write_text("second new report")

        plan = utils.get_sort_plan(
            str(self.downloads),
            [self.make_rule("Text", "Documents", extensions=[".txt"])],
        )

        destinations = [destination_path for _, destination_path in plan]
        self.assertEqual(len(plan), 2)
        self.assertEqual(len(set(destinations)), 2)
        self.assertTrue(first_source.is_file())
        self.assertTrue(second_source.is_file())


if __name__ == "__main__":
    unittest.main()

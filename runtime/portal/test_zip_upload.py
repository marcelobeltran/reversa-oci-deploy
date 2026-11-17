import io
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import zip_upload


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.destination = self.root / "source"
        self.destination.mkdir()
        self.archive = self.root / "upload.zip"

    def write(self, entries):
        with zipfile.ZipFile(self.archive, "w") as archive:
            for name, content in entries:
                archive.writestr(name, content)

    def test_valid_wrapper_and_hidden_files(self):
        self.write([("repo/main.py", "print('ok')"), ("repo/src/lib.py", "x=1"), ("repo/.env", "secret"), ("repo/node_modules/a.js", "unused")])
        self.assertEqual(zip_upload.extract_archive(self.archive, self.destination), 2)
        self.assertTrue((self.destination / "main.py").is_file())
        self.assertTrue((self.destination / "src/lib.py").is_file())
        self.assertFalse((self.destination / ".env").exists())

    def test_traversal_and_absolute_paths(self):
        for name in ("../outside.txt", "/outside.txt", "C:/outside.txt", "repo/../x"):
            with self.subTest(name=name):
                self.write([(name, "unsafe")])
                with self.assertRaises(ValueError):
                    zip_upload.extract_archive(self.archive, self.destination)
        self.assertFalse((self.root / "outside.txt").exists())

    def test_backslash_paths(self):
        # Windows ZipFile normalizes backslashes when writing; mutate both headers.
        self.write([("repo/outside.txt", "unsafe")])
        self.archive.write_bytes(self.archive.read_bytes().replace(b"repo/outside.txt", b"repo\\outside.txt"))
        with self.assertRaises(ValueError):
            zip_upload.extract_archive(self.archive, self.destination)

    def test_symlinks_rejected(self):
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.write([(info, "/etc/passwd")])
        with self.assertRaises(ValueError):
            zip_upload.extract_archive(self.archive, self.destination)

    def test_duplicate_case_paths_rejected_before_write(self):
        self.write([("repo/A.py", "one"), ("repo/a.py", "two")])
        with self.assertRaises(ValueError):
            zip_upload.extract_archive(self.archive, self.destination)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_expansion_limit(self):
        self.write([("large.txt", "12345")])
        with patch.object(zip_upload, "MAX_EXPANDED", 4):
            with self.assertRaises(ValueError):
                zip_upload.extract_archive(self.archive, self.destination)

    def test_entry_limit(self):
        self.write([("a.txt", "a"), ("b.txt", "b")])
        with patch.object(zip_upload, "MAX_FILES", 1):
            with self.assertRaises(ValueError):
                zip_upload.extract_archive(self.archive, self.destination)

    def test_multiple_root_files_preserved(self):
        self.write([("a.py", "one"), ("src/b.py", "two")])
        zip_upload.extract_archive(self.archive, self.destination)
        self.assertTrue((self.destination / "a.py").exists())
        self.assertTrue((self.destination / "src/b.py").exists())


if __name__ == "__main__":
    unittest.main()

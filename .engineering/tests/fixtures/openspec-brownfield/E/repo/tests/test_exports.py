import unittest

from src.exports import export_rows


class ExportTests(unittest.TestCase):
    def test_rows(self):
        self.assertEqual(export_rows(["one", "two"]), "one\ntwo")

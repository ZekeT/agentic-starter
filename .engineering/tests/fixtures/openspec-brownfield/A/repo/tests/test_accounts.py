import unittest

from src.accounts import locked


class AccountTests(unittest.TestCase):
    def test_lock_boundary(self):
        self.assertFalse(locked(4))
        self.assertTrue(locked(5))

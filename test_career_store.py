import unittest

from backend.career_store import MemoryCareerStore
from backend.season_api import Career


class CareerStoreTests(unittest.TestCase):
    def test_user_without_save_has_no_career(self):
        store = MemoryCareerStore()
        self.assertIsNone(store.load(10))

    def test_each_user_loads_their_own_week(self):
        store = MemoryCareerStore()
        career_a = Career()
        career_b = Career()

        result = career_a.season.advance_week(1, rng=career_a.rng)
        self.assertTrue(result["valid"])

        store.save(10, career_a)
        store.save(20, career_b)

        self.assertEqual(store.load(10).season.next_week, 2)
        self.assertEqual(store.load(20).season.next_week, 1)

    def test_loaded_changes_are_saved_only_when_requested(self):
        store = MemoryCareerStore()
        store.save(10, Career())

        loaded = store.load(10)
        result = loaded.season.advance_week(1, rng=loaded.rng)
        self.assertTrue(result["valid"])

        self.assertEqual(store.load(10).season.next_week, 1)

        store.save(10, loaded)
        self.assertEqual(store.load(10).season.next_week, 2)
import unittest
from unittest.mock import patch

from backend import season_api as api
from backend.career_store import MemoryCareerStore


class CareerApiStoreTests(unittest.TestCase):
    def setUp(self):
        self.user = {"user_id": 11}
        self.store = MemoryCareerStore()
        self.enterContext(patch.object(api, "user_careers", {}))
        self.enterContext(patch.object(api, "career_store", self.store))
        self.career = api.get_user_career(self.user)
        self.edit = api.user_editor(self.user)

    def test_reload_saved_week_after_cache_clear(self):
        with self.edit(self.career) as working:
            result = working.season.advance_week(1, rng=working.rng)
            self.assertTrue(result["valid"])
        api.user_careers.clear()
        restored = api.get_user_career(self.user)
        self.assertEqual(restored.season.next_week, 2)
        self.assertEqual(len(restored.season.completed_matches), 2)

    def test_failed_save_keeps_original_week(self):
        with patch.object(self.store, "save", side_effect=OSError("save failed")):
            with self.assertRaises(OSError):
                with self.edit(self.career) as working:
                    working.season.advance_week(1, rng=working.rng)
        self.assertEqual(self.career.season.next_week, 1)
        self.assertEqual(self.store.load(11).season.next_week, 1)

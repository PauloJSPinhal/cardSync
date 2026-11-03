import unittest, tempfile, os
from cardsync.core.importer import group_files, classify, list_supported, RAW_EXTS, JPG_EXTS


class TestImporter(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify("a.CR2"), "01_RAW")
        self.assertEqual(classify("a.jpg"), "02_JPG_Original")
        self.assertEqual(classify("a.jpg", treated=True), "03_Tratadas")
        self.assertIsNone(classify("a.txt"))

    def test_group_files_splits_by_date(self):
        # usar resolver de data fixo
        def resolver(p):
            from datetime import date
            if "day2" in p:
                return date(2026, 11, 4)
            return date(2026, 11, 3)
        paths = ["/x/a.CR2", "/x/day2_b.JPG"]
        g = group_files(paths, "Evento", "Local", target_date=None, shot_date_resolver=resolver)
        self.assertEqual(len(g), 2)
        self.assertIn("20261103_Evento_Local", g)
        self.assertIn("20261104_Evento_Local", g)

    def test_list_supported(self):
        self.assertEqual(list_supported(["a.cr2", "b.txt", "c.JPG"]), ["a.cr2", "c.JPG"])


if __name__ == "__main__":
    unittest.main()
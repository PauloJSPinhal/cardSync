import unittest
from cardsync.core.naming import sanitize, folder_name, display_title, project_id, format_date_yyyymmdd


class TestNaming(unittest.TestCase):
    def test_sanitize(self):
        self.assertEqual(sanitize("Feira Gandarola"), "Feira-Gandarola")
        self.assertEqual(sanitize("  a  b  "), "a-b")
        self.assertEqual(sanitize("Cantanhede!"), "Cantanhede")

    def test_folder_name(self):
        self.assertEqual(folder_name("20261103", "Feira Gandarola", "Febres"),
                         "20261103_Feira-Gandarola_Febres")
        self.assertEqual(folder_name("2026-11-03", "Feira Gandarola", "Febres"),
                         "20261103_Feira-Gandarola_Febres")

    def test_display_title(self):
        self.assertEqual(display_title("20261103", "Feira Gandarola", "Febres"),
                         "03/11/2026 — Feira Gandarola, Febres")

    def test_project_id(self):
        self.assertEqual(project_id("20261103", "Feira Gandarola"),
                         "proj_20261103_feira_gandarola")

    def test_format_date(self):
        self.assertEqual(format_date_yyyymmdd("03/11/2026"), "20261103")


if __name__ == "__main__":
    unittest.main()
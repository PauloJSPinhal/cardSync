import unittest, tempfile, os, hashlib
from cardsync.core.backend.local import LocalBackend
from cardsync.core.collection import create_collection, upload_files
from cardsync.core.hashing import md5_file


class TestLocalBackend(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.b = LocalBackend(self.d)

    def test_auth(self):
        self.assertTrue(self.b.authenticate())
        self.assertTrue(self.b.is_authenticated())

    def test_structure_and_upload_dedup(self):
        col = create_collection(self.b, "20261103", "Evento", "Local")
        manifest = col["manifest"]
        # criar ficheiro local
        fd, path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        with open(path, "wb") as f:
            f.write(b"hello world")
        grouped = {col["root_name"]: {"02_JPG_Original": [path]}}
        res1 = upload_files(self.b, manifest, grouped, dedup=False)
        self.assertEqual(res1["uploaded"], 1)
        # segundo upload com dedup
        res2 = upload_files(self.b, manifest, grouped, dedup=True)
        self.assertEqual(res2["skipped"], 1)
        self.assertEqual(res2["uploaded"], 0)

    def test_find_folder(self):
        self.b.create_folder("X")
        self.assertIsNotNone(self.b.find_folder("X"))
        self.assertIsNone(self.b.find_folder("Y"))


if __name__ == "__main__":
    unittest.main()
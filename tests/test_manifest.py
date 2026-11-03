import unittest, tempfile, os, json
from cardsync.core.manifest import new_manifest, save_manifest, load_manifest, add_file_entry, set_status, add_shared


class TestManifest(unittest.TestCase):
    def test_new_and_save(self):
        m = new_manifest("proj_x", "20261103_E_L", "03/11/2026 — E, L")
        self.assertEqual(m["status"], "active")
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        save_manifest(path, m)
        m2 = load_manifest(path)
        self.assertEqual(m2["project_id"], "proj_x")
        os.remove(path)

    def test_add_file_entry_dedup(self):
        m = new_manifest("p", "f", "t")
        add_file_entry(m, "a.CR2", "RAW", 100, "md5a")
        add_file_entry(m, "a.CR2", "RAW", 100, "md5a")
        self.assertEqual(len(m["files_manifest"]), 1)

    def test_status_and_shared(self):
        m = new_manifest("p", "f", "t")
        set_status(m, "frozen")
        self.assertEqual(m["status"], "frozen")
        add_shared(m, "a@b.pt", "perm1")
        self.assertEqual(len(m["shared_with"]), 1)
        add_shared(m, "a@b.pt", "perm2")
        self.assertEqual(len(m["shared_with"]), 1)


if __name__ == "__main__":
    unittest.main()
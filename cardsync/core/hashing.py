"""Cálculo de hash MD5 (secção 3.4)."""

import hashlib
import os


def md5_file(path: str, chunk_size: int = 8192) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def file_size(path: str) -> int:
    return os.path.getsize(path)